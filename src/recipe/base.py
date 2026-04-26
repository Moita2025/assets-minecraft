import json
from collections import Counter
from pathlib import Path

from configs import MERGED_JSON_FILE

def get_original_recipes():

    # 指定路径
    file_path = Path(MERGED_JSON_FILE)

    # 读取 JSON 文件
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)  # 假设是一个数组

    return data

def get_recipes_type_dist(data):

    # 提取所有 type 字段
    types = [item["type"] for item in data if "type" in item]

    # 统计频率
    type_count = Counter(types)

    # 输出结果
    for t, count in type_count.items():
        print(f"{t}: {count}")

if __name__ == "__main__":

    from tag.base import (
        split_recipes_by_tag, 
        get_recipes_tag_dist
    )

    data = get_original_recipes()

    print("=== 类型统计 ===")
    get_recipes_type_dist(data)

    with_tag, without_tag = split_recipes_by_tag(data)
    print("\n=== 含 #minecraft: 的 tag 统计 ===")
    get_recipes_tag_dist(with_tag)
    print(f"\n包含 tag 的数量: {len(with_tag)}")
    print(f"不包含 tag 的数量: {len(without_tag)}")