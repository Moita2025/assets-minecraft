"""
把 tag 信息内嵌到 1.21.11/config.json 的每条记录中。

来源：tag/dict.py:get_tags_list_dict() 提供的 `tag_name -> [item_ids]` 解析结果。
反向构建 `item_id -> [tag_refs]`，再把 `tags` 字段写到 config.json 数组每个 dict 元素中
（紧跟在 idDetails 之后），值形如 ["#minecraft:planks", "#minecraft:logs"]。

幂等：每次都基于源数据重算后排序，相同数据多次运行不会产生 diff。

CLI:
    python src/tag/embed.py                 # 写入 ID_JSON_FILE
    python src/tag/embed.py --dry-run       # 仅统计，不写盘
    python src/tag/embed.py --path <rel>    # 处理其他 config.json（前提：里面条目带 idDetails）
"""
import argparse
import json
from pathlib import Path

from configs import ID_JSON_FILE, DEFAULT_NAMESPACE
from tag.dict import get_tags_list_dict
from tag.refs import normalize_resource_ref, to_tag_ref

TAGS_KEY = "tags"
TAGS_INSERT_AFTER = "idDetails"

REPO_ROOT = Path(__file__).resolve().parents[2]


def build_item_tag_index(tags_list_dict, default_namespace=DEFAULT_NAMESPACE):
    """
    把 `tag_name -> [item_ids]` 翻转成 `normalized_item_id -> sorted [tag_refs]`。
    tag_refs 带 `#` 前缀（与配方里的引用形式一致）。
    """
    index = {}
    for tag_name, items in tags_list_dict.items():
        tag_ref = to_tag_ref(tag_name)
        if tag_ref is None:
            continue
        for item in items:
            normalized = normalize_resource_ref(item, default_namespace)
            if normalized is None:
                continue
            index.setdefault(normalized, set()).add(tag_ref)
    return {k: sorted(v) for k, v in index.items()}


def _reorder_with_tags(item, tags):
    """返回新的 dict：移除任意位置的旧 tags，再插入到 idDetails 之后。"""
    new_item = {}
    inserted = False
    for key, value in item.items():
        if key == TAGS_KEY:
            continue
        new_item[key] = value
        if key == TAGS_INSERT_AFTER:
            new_item[TAGS_KEY] = tags
            inserted = True
    if not inserted:
        # 没有 idDetails：按需追加到末尾（理论上调用方已过滤）
        new_item[TAGS_KEY] = tags
    return new_item


def _resolve_item_id(item):
    """从条目里取出最后一个 idDetails 的 englishId，并 normalize。无则返回 None。"""
    id_details = item.get("idDetails")
    if not isinstance(id_details, list) or not id_details:
        return None
    last = id_details[-1]
    if not isinstance(last, dict):
        return None
    english_id = last.get("englishId")
    return normalize_resource_ref(english_id)


def embed_tags(items, item_tag_index):
    """
    对 items（顶层 JSON 数组的元素列表）原地写入 tags 字段。
    返回 stats:
        - updated:        tags 内容相比原值发生变化（含从无到有）
        - unchanged:      tags 内容与原值一致
        - skipped_no_id:  没有 idDetails / englishId
        - skipped_non_dict: 非 dict 元素
    """
    stats = {
        "updated": 0,
        "unchanged": 0,
        "skipped_no_id": 0,
        "skipped_non_dict": 0,
    }

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            stats["skipped_non_dict"] += 1
            continue

        normalized_id = _resolve_item_id(item)
        if normalized_id is None:
            stats["skipped_no_id"] += 1
            continue

        new_tags = item_tag_index.get(normalized_id, [])
        old_tags = item.get(TAGS_KEY)

        if old_tags == new_tags:
            stats["unchanged"] += 1
        else:
            stats["updated"] += 1

        items[idx] = _reorder_with_tags(item, new_tags)

    return stats


def embed_tags_into_config(rel_path, dry_run=False):
    full_path = (REPO_ROOT / rel_path).resolve()
    with full_path.open("r", encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise ValueError(f"{rel_path}: 顶层不是 JSON 数组")

    tags_list_dict = get_tags_list_dict()
    item_tag_index = build_item_tag_index(tags_list_dict)

    stats = embed_tags(items, item_tag_index)

    if not dry_run:
        with full_path.open("w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=4)
            f.write("\n")
    return stats, len(item_tag_index)


def main():
    parser = argparse.ArgumentParser(
        description="把 tag 反向写入 config.json 的每个条目"
    )
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写盘")
    parser.add_argument(
        "--path",
        default=ID_JSON_FILE,
        help=f"目标 config.json 相对路径（默认 {ID_JSON_FILE}）",
    )
    args = parser.parse_args()

    stats, indexed_items = embed_tags_into_config(args.path, dry_run=args.dry_run)
    marker = "[DRY] " if args.dry_run else "[OK]  "
    total = stats["updated"] + stats["unchanged"]
    with_tags = stats["updated"] + stats["unchanged"]
    print(
        f"{marker}{args.path}  "
        f"updated={stats['updated']}  unchanged={stats['unchanged']}  "
        f"skipped_no_id={stats['skipped_no_id']}  skipped_non_dict={stats['skipped_non_dict']}  "
        f"(写出 {with_tags}/{total} 条 tags 字段；反向索引覆盖 {indexed_items} 个物品)"
    )


if __name__ == "__main__":
    main()
