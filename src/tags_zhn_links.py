import json
from pathlib import Path

from recipes_analysis import get_all_tags
from configs import TAGS_INPUT_DIRECTORIES, ID_JSON_FILE

def get_tags_list_dict():
    tags = get_all_tags()
    tags_list_dict = {}

    base_paths = [Path(p) for p in TAGS_INPUT_DIRECTORIES]

    for tag in tags:
        found_file = None

        # 在多个目录中查找
        for base_path in base_paths:
            file_path = base_path / f"{tag}.json"
            if file_path.exists():
                found_file = file_path
                break  # 找到第一个就用

        # 没找到 → 报错
        if not found_file:
            raise FileNotFoundError(
                f"缺少 tag 文件: {tag}.json，已搜索目录: {TAGS_INPUT_DIRECTORIES}"
            )

        # 读取 JSON
        with open(found_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 校验 values
        if "values" not in data:
            raise KeyError(f"{found_file} 缺少 'values' 字段")

        if not isinstance(data["values"], list):
            raise TypeError(f"{found_file} 的 'values' 不是数组")

        tags_list_dict[tag] = data["values"]

    return tags_list_dict

def get_tags_zhn_list_dict():
    tags_list_dict = get_tags_list_dict()

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

    result = get_tags_zhn_list_dict()

    pretty_json = json.dumps(
        result,
        indent=4,                # 四空格缩进
        ensure_ascii=False,      # 保持中文不被转义（如果你想让中文原样输出）
    )

    # 在终端中打印
    print(pretty_json)