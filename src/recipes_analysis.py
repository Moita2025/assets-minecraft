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

def contains_minecraft_tag(obj):
    """
    递归检查任意对象中是否包含 '#minecraft:' 子串
    """
    if isinstance(obj, dict):
        return any(contains_minecraft_tag(v) for v in obj.values())
    elif isinstance(obj, list):
        return any(contains_minecraft_tag(i) for i in obj)
    elif isinstance(obj, str):
        return "#minecraft:" in obj
    return False


def split_recipes_by_tag(data):
    """
    将 data 拆分为：
    - 包含 #minecraft:
    - 不包含 #minecraft:
    """
    with_tag = []
    without_tag = []

    for item in data:
        if contains_minecraft_tag(item):
            with_tag.append(item)
        else:
            without_tag.append(item)

    return with_tag, without_tag


def get_recipes_tag_dist(data, print = True):
    """
    统计 '#minecraft:' 出现的频率
    """
    tag_counter = Counter()

    def extract_tags(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                extract_tags(v)
        elif isinstance(obj, list):
            for i in obj:
                extract_tags(i)
        elif isinstance(obj, str):
            if "#minecraft:" in obj:
                tag_counter[obj] += 1

    for item in data:
        extract_tags(item)

    if (print):
        # 输出统计
        for tag, count in tag_counter.items():
            print(f"{tag}: {count}")

    return tag_counter

def get_all_tags(prefix = "#minecraft:"):

    data = get_original_recipes()
    with_tag, _ = split_recipes_by_tag(data)
    tag_counter = get_recipes_tag_dist(with_tag, print=False)

    # 去重 + 去掉前缀
    cleaned_tags = [
        tag[len(prefix):] if tag.startswith(prefix) else tag
        for tag in tag_counter.keys()
    ]

    return sorted(cleaned_tags)


if __name__ == "__main__":

    data = get_original_recipes()

    print("=== 类型统计 ===")
    get_recipes_type_dist(data)

    with_tag, without_tag = split_recipes_by_tag(data)
    print("\n=== 含 #minecraft: 的 tag 统计 ===")
    get_recipes_tag_dist(with_tag)
    print(f"\n包含 tag 的数量: {len(with_tag)}")
    print(f"不包含 tag 的数量: {len(without_tag)}")