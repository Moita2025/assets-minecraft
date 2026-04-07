import json
from pathlib import Path

from configs import TAGS_INPUT_DIRECTORIES, ID_JSON_FILE

def load_all_tags():
    base_paths = [Path(p) for p in TAGS_INPUT_DIRECTORIES]
    tag_map = {}

    for base_path in base_paths:
        for file in base_path.glob("*.json"):
            tag_name = file.stem  # 不带 .json

            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "values" not in data or not isinstance(data["values"], list):
                continue

            tag_map[tag_name] = data["values"]

    return tag_map

def resolve_tag(tag, tag_map, cache, visiting, path=None, output = False):
    
    if path is None:
        path = []

    if (output):
        print(f"Resolving: {' -> '.join(path + [tag])}")
    
    # 已缓存
    if tag in cache:
        return cache[tag]

    # 检测循环引用
    if tag in visiting:
        cycle_path = " -> ".join(path + [tag])
        raise ValueError(f"检测到循环引用: {tag}")

    visiting.add(tag)
    path.append(tag)

    result = []

    for v in tag_map.get(tag, []):
        if isinstance(v, str) and v.startswith("#minecraft:"):
            sub_tag = v.replace("#minecraft:", "")
            result.extend(resolve_tag(sub_tag, tag_map, cache, visiting, path))
        else:
            result.append(v)

    path.pop()
    visiting.remove(tag)

    # 去重（可选）
    result = list(dict.fromkeys(result))

    cache[tag] = result
    return result

def get_tags_list_dict(output = False):
    tag_map = load_all_tags()

    resolved = {}
    cache = {}

    for tag in tag_map:
        resolved[tag] = resolve_tag(tag, tag_map, cache, set(), output = output)

    return resolved

def get_en2zh_dict():
    # 读取 ID 映射表
    with open(ID_JSON_FILE, "r", encoding="utf-8") as f:
        id_data = json.load(f)

    # 构建 englishId -> 中文 的映射
    en_to_zh = {}

    for item in id_data:
        if "idDetails" not in item or not item["idDetails"]:
            continue

        last = item["idDetails"][-1]

        if "englishId" in last:
            en = last["englishId"]
            zh = item.get("chineseName", en)  # fallback
            en_to_zh[en] = zh

    return en_to_zh

def get_tags_zhn_list_dict(output = True):
    tags_list_dict = get_tags_list_dict(output)

    en_to_zh = get_en2zh_dict()

    # 转换 tags_list_dict
    tags_zhn_list_dict = {}

    for tag, values in tags_list_dict.items():
        new_values = []

        for v in values:
            # 如果是字符串，直接映射
            if isinstance(v, str):
                new_values.append(en_to_zh.get(v, v))
            else:
                # 如果是复杂结构，保留原样（也可以改成递归）
                new_values.append(v)

        key_name = f"#minecraft:{tag}" if not tag.startswith("#minecraft:") else tag

        tags_zhn_list_dict[key_name] = new_values

    return tags_zhn_list_dict

if __name__ == "__main__":

    result = get_tags_zhn_list_dict(output = True)

    pretty_json = json.dumps(
        result,
        indent=4,                # 四空格缩进
        ensure_ascii=False,      # 保持中文不被转义（如果你想让中文原样输出）
    )

    # 在终端中打印
    print(pretty_json)