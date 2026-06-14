"""
把所有 tag 的名字 dump 成扁平字符串数组，写入 tags.json。

输出形如：
    [
        "#minecraft:acacia_logs",
        "#minecraft:acacia_planks",
        ...
    ]

只回答"有哪些 tag"。每个 tag 具体包含哪些物品，已经内嵌在
1.21.11/config.json 各条目的 tags 字段里（见 src/tag/embed.py）。

CLI:
    python src/tag/dump.py                 # 默认写到 TAG_JSON_FILE
    python src/tag/dump.py --dry-run       # 只统计，不写盘
    python src/tag/dump.py --path <rel>    # 指定其他输出路径
"""
import argparse
import json
from pathlib import Path

from configs import TAG_JSON_FILE
from tag.dict import get_tags_list_dict
from tag.refs import to_tag_ref

REPO_ROOT = Path(__file__).resolve().parents[2]


def get_all_tag_refs():
    """返回去重 + 字典序排序后的 #namespace:path 列表。"""
    tags_list_dict = get_tags_list_dict()
    refs = set()
    for name in tags_list_dict:
        ref = to_tag_ref(name)
        if ref:
            refs.add(ref)
    return sorted(refs)


def dump_tag_refs(rel_path=TAG_JSON_FILE, dry_run=False):
    refs = get_all_tag_refs()
    full_path = (REPO_ROOT / rel_path).resolve()

    if not dry_run:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with full_path.open("w", encoding="utf-8") as f:
            json.dump(refs, f, ensure_ascii=False, indent=4)
            f.write("\n")
    return refs


def main():
    parser = argparse.ArgumentParser(
        description="把所有 tag 名 dump 成 JSON 字符串数组"
    )
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写盘")
    parser.add_argument(
        "--path",
        default=TAG_JSON_FILE,
        help=f"输出路径（相对仓库根，默认 {TAG_JSON_FILE}）",
    )
    args = parser.parse_args()

    refs = dump_tag_refs(args.path, dry_run=args.dry_run)
    marker = "[DRY] " if args.dry_run else "[OK]  "
    print(f"{marker}{args.path}  count={len(refs)}")


if __name__ == "__main__":
    main()
