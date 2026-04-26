from collections import Counter

from configs import DEFAULT_TAG_PREFIX

def contains_minecraft_tag(obj, prefix=DEFAULT_TAG_PREFIX):
    """
    递归检查任意对象中是否包含 'prefix' 子串
    """
    if isinstance(obj, dict):
        return any(contains_minecraft_tag(v) for v in obj.values())
    elif isinstance(obj, list):
        return any(contains_minecraft_tag(i) for i in obj)
    elif isinstance(obj, str):
        return prefix in obj
    return False


def split_recipes_by_tag(data, prefix=DEFAULT_TAG_PREFIX):
    """
    将 data 拆分为：
    - 包含 prefix
    - 不包含 prefix
    """
    with_tag = []
    without_tag = []

    for item in data:
        if contains_minecraft_tag(item, prefix):
            with_tag.append(item)
        else:
            without_tag.append(item)

    return with_tag, without_tag


def get_recipes_tag_dist(data, prefix=DEFAULT_TAG_PREFIX, output=True):
    """
    统计 'prefix' 出现的频率
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
            if prefix in obj:
                tag_counter[obj] += 1

    for item in data:
        extract_tags(item)

    if (output):
        # 输出统计
        for tag, count in tag_counter.items():
            print(f"{tag}: {count}")

    return tag_counter

def get_all_tags(prefix=DEFAULT_TAG_PREFIX):

    from recipe.base import get_original_recipes

    data = get_original_recipes()
    with_tag, _ = split_recipes_by_tag(data, prefix)
    tag_counter = get_recipes_tag_dist(with_tag, prefix, print=False)

    # 去重 + 去掉前缀
    cleaned_tags = [
        tag[len(prefix):] if tag.startswith(prefix) else tag
        for tag in tag_counter.keys()
    ]

    return sorted(cleaned_tags)