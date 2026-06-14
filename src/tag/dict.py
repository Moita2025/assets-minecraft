"""
读取 vanilla tag 目录，递归解析嵌套 tag 引用，得到 `tag_name -> [item_ids]` 的字典。

不再生成独立的 tags.json；这个模块只负责构建解析后的字典，
反向写入 config.json 的逻辑见 src/tag/embed.py。
"""
import json
from pathlib import Path

from configs import (
    TAGS_INPUT_DIRECTORIES,
    DEFAULT_NAMESPACE,
)
from tag.refs import normalize_tag_ref


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


def resolve_tag(tag, tag_map, cache, visiting, path=None, output=False):
    if path is None:
        path = []

    if output:
        print(f"Resolving: {' -> '.join(path + [tag])}")

    if tag in cache:
        return cache[tag]

    if tag in visiting:
        cycle_path = " -> ".join(path + [tag])
        raise ValueError(f"检测到循环引用: {cycle_path}")

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

    # 去重，保留首次出现顺序
    result = list(dict.fromkeys(result))

    cache[tag] = result
    return result


def get_tags_list_dict(output=False):
    tag_map = load_all_tags()

    resolved = {}
    cache = {}

    for tag in tag_map:
        resolved[tag] = resolve_tag(tag, tag_map, cache, set(), output=output)

    return resolved


if __name__ == "__main__":
    d = get_tags_list_dict()
    print(f"已解析 {len(d)} 个 tag")
    sample = next(iter(d.items()))
    print(f"示例: {sample[0]} -> {sample[1][:5]}{' ...' if len(sample[1]) > 5 else ''}")
