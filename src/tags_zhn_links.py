import json
from pathlib import Path

from configs import (
    TAGS_INPUT_DIRECTORIES,
    ID_JSON_FILE,
    TAG_JSON_FILE,
    DEFAULT_NAMESPACE,
)
from refs import normalize_tag_ref, to_tag_ref

def load_all_tags():
    base_paths = [Path(p) for p in TAGS_INPUT_DIRECTORIES]
    tag_map = {}

    for base_path in base_paths:
        for file in base_path.rglob("*.json"):
            tag_name = get_namespaced_tag_name(base_path, file)

            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "values" not in data or not isinstance(data["values"], list):
                continue

            tag_map[tag_name] = data["values"]

    return tag_map


def get_namespaced_tag_name(base_path, file_path):
    """
    根据目录结构解析命名空间，统一返回 namespace:path 形式。
    支持目录形如 data/<namespace>/tags/<kind>/.../*.json。
    """
    relative_stem = file_path.relative_to(base_path).with_suffix("").as_posix()
    namespace = DEFAULT_NAMESPACE
    parts = file_path.parts
    if "data" in parts:
        data_index = parts.index("data")
        if data_index + 1 < len(parts):
            namespace = parts[data_index + 1]
    return f"{namespace}:{relative_stem}"


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
        parsed_tag = normalize_tag_ref(v)
        if parsed_tag:
            result.extend(resolve_tag(parsed_tag, tag_map, cache, visiting, path))
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

        key_name = to_tag_ref(tag) if not tag.startswith("#") else tag

        tags_zhn_list_dict[key_name] = new_values

    return tags_zhn_list_dict

def format_list(lst, indent=4):
    # 少于5个：一行
    if len(lst) < 5:
        return json.dumps(lst, ensure_ascii=False)
    
    # >=5个：多行，每10个一行
    lines = []
    for i in range(0, len(lst), 10):
        chunk = lst[i:i+10]
        line = ', '.join(json.dumps(x, ensure_ascii=False) for x in chunk)
        lines.append(' ' * indent + line)
    
    return '[\n' + ',\n'.join(lines) + '\n]'

def save_result(result, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('{\n')
        
        items = list(result.items())
        for idx, (key, value) in enumerate(items):
            f.write(f'    {json.dumps(key, ensure_ascii=False)}: ')
            f.write(format_list(value, indent=8))
            
            if idx != len(items) - 1:
                f.write(',')
            f.write('\n')
        
        f.write('}\n')

def get_tag_dict(output = False):
    result = get_tags_zhn_list_dict(output = output)

    pretty_json = json.dumps(
        result,
        indent=4,                
        ensure_ascii=False,      
    )
    if (output): print(pretty_json)

    save_result(result, TAG_JSON_FILE)


if __name__ == "__main__":

    get_tag_dict()