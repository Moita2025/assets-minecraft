import json
from pathlib import Path

from recipes_analysis import get_all_tags
from configs import TAGS_INPUT_DIRECTORY, ID_JSON_FILE

def get_tags_list_dict():
    tags = get_all_tags()
    tags_list_dict = {}

    base_path = Path(TAGS_INPUT_DIRECTORY)

    for tag in tags:
        file_path = base_path / f"{tag}.json"

        # 文件不存在 → 报错并中止
        if not file_path.exists():
            raise FileNotFoundError(f"缺少 tag 文件: {file_path}")

        # 读取 JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 校验 values
        if "values" not in data:
            raise KeyError(f"{file_path} 缺少 'values' 字段")

        if not isinstance(data["values"], list):
            raise TypeError(f"{file_path} 的 'values' 不是数组")

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

        tags_zhn_list_dict[tag] = new_values

    return tags_zhn_list_dict

if __name__ == "__main__":
    
    print(get_tags_zhn_list_dict())