from configs import DEFAULT_NAMESPACE


def is_tag_ref(value):
    return isinstance(value, str) and value.startswith("#")


def normalize_resource_ref(value, default_namespace=DEFAULT_NAMESPACE):
    """
    标准化资源引用，返回 namespace:path。
    例如:
    - minecraft:stone -> minecraft:stone
    - stone -> minecraft:stone
    """
    if not isinstance(value, str) or not value:
        return None
    if ":" in value:
        return value
    return f"{default_namespace}:{value}"


def normalize_tag_ref(tag_ref, default_namespace=DEFAULT_NAMESPACE):
    """
    标准化 tag 引用，返回 namespace:path（不带 #）。
    例如:
    - #forge:ingots/iron -> forge:ingots/iron
    - #planks -> minecraft:planks
    """
    if not is_tag_ref(tag_ref):
        return None
    return normalize_resource_ref(tag_ref[1:], default_namespace=default_namespace)


def to_tag_ref(tag_key):
    """
    将 namespace:path 转换为 #namespace:path。
    """
    normalized = normalize_resource_ref(tag_key)
    if not normalized:
        return None
    return f"#{normalized}"
