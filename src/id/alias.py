"""
Alias ID 管理：为各 config.json 数组元素分配 / 补全 aliasID。

形式：<namespace>:<2 个 base62 字符>
- namespace 来自 configs.ALIAS_CONFIGS（如 mc / twf / zhwiki）
- 字符表为 0-9 + A-Z + a-z 共 62 字符，2 位长度合计 3844 个槽位

幂等性：
- 已合法且文件内不重复的 aliasID 会被原样保留
- 缺失 / 格式错误 / 命名空间不匹配 / 同文件内重复 的会按字典序补一个未占用的
- 数组元素顺序不变；元素内键顺序会规范化为 aliasID 紧跟在 chineseName 之后

CLI:
    python src/id/alias.py                 # 处理 ALIAS_CONFIGS 全部
    python src/id/alias.py --dry-run       # 仅统计，不写盘
    python src/id/alias.py --path <rel> --namespace <ns>   # 处理单个文件
"""
import argparse
import json
import string
from pathlib import Path

from configs import ALIAS_CONFIGS

ALIAS_ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase
ALIAS_LENGTH = 2
ALIAS_KEY = "aliasID"
ALIAS_INSERT_AFTER = "chineseName"

# src/id/alias.py -> parents[2] 是仓库根
REPO_ROOT = Path(__file__).resolve().parents[2]

ALIAS_CAPACITY = len(ALIAS_ALPHABET) ** ALIAS_LENGTH


def _is_valid_alias(alias, namespace):
    if not isinstance(alias, str):
        return False
    prefix = f"{namespace}:"
    if not alias.startswith(prefix):
        return False
    suffix = alias[len(prefix):]
    if len(suffix) != ALIAS_LENGTH:
        return False
    return all(c in ALIAS_ALPHABET for c in suffix)


def _iter_suffixes():
    """按字典序遍历所有 base62 后缀（从 '00' 到 'zz'）。"""
    for a in ALIAS_ALPHABET:
        for b in ALIAS_ALPHABET:
            yield a + b


def _reorder_with_alias(item, alias):
    """返回新的 dict：移除任意位置的旧 aliasID，再插入到 chineseName 之后。"""
    new_item = {}
    inserted = False
    for key, value in item.items():
        if key == ALIAS_KEY:
            continue
        new_item[key] = value
        if key == ALIAS_INSERT_AFTER:
            new_item[ALIAS_KEY] = alias
            inserted = True
    if not inserted:
        new_item = {ALIAS_KEY: alias, **new_item}
    return new_item


def assign_aliases(items, namespace):
    """
    给数组 items 分配 aliasID，原地修改其元素。
    返回 stats：{"kept", "new", "reassigned", "skipped"}。
    """
    used = set()
    needs_new = []
    stats = {"kept": 0, "new": 0, "reassigned": 0, "skipped": 0}

    # Pass 1：保留合法且不重复的 aliasID
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            stats["skipped"] += 1
            continue
        alias = item.get(ALIAS_KEY)
        if alias is not None and _is_valid_alias(alias, namespace) and alias not in used:
            used.add(alias)
            stats["kept"] += 1
        else:
            needs_new.append((idx, alias))

    # 容量预检
    total_needed = len(used) + len(needs_new)
    if total_needed > ALIAS_CAPACITY:
        raise RuntimeError(
            f"namespace '{namespace}' 容量不足：需要 {total_needed} 个，"
            f"但 {ALIAS_LENGTH} 位 base62 仅支持 {ALIAS_CAPACITY} 个。"
            f"请考虑扩容（增加位数或拆分命名空间）。"
        )

    # Pass 2：按字典序补 / 重发
    suffix_gen = _iter_suffixes()
    for idx, old_alias in needs_new:
        new_alias = None
        for suffix in suffix_gen:
            candidate = f"{namespace}:{suffix}"
            if candidate not in used:
                used.add(candidate)
                new_alias = candidate
                break
        if new_alias is None:
            raise RuntimeError(f"namespace '{namespace}' 别名空间已耗尽")
        items[idx][ALIAS_KEY] = new_alias
        if old_alias in (None, ""):
            stats["new"] += 1
        else:
            stats["reassigned"] += 1

    # Pass 3：规范化所有元素的键顺序
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        alias = item.get(ALIAS_KEY)
        if alias is None:
            continue
        items[idx] = _reorder_with_alias(item, alias)

    return stats


def process_config(rel_path, namespace, dry_run=False):
    full_path = (REPO_ROOT / rel_path).resolve()
    with full_path.open("r", encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise ValueError(f"{rel_path}: 顶层不是 JSON 数组")

    stats = assign_aliases(items, namespace)

    if not dry_run:
        with full_path.open("w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=4)
            f.write("\n")
    return stats


def process_all(dry_run=False):
    overall = {}
    for cfg in ALIAS_CONFIGS:
        rel_path = cfg["path"]
        namespace = cfg["namespace"]
        full_path = (REPO_ROOT / rel_path).resolve()
        if not full_path.exists():
            print(f"[SKIP] 不存在: {rel_path}")
            continue

        stats = process_config(rel_path, namespace, dry_run=dry_run)
        overall[rel_path] = stats

        marker = "[DRY] " if dry_run else "[OK]  "
        total = stats["kept"] + stats["new"] + stats["reassigned"]
        capacity_pct = total * 100 / ALIAS_CAPACITY
        print(
            f"{marker}{namespace:>6}  {rel_path}  "
            f"kept={stats['kept']}  new={stats['new']}  "
            f"reassigned={stats['reassigned']}  skipped={stats['skipped']}  "
            f"({total}/{ALIAS_CAPACITY}, {capacity_pct:.1f}%)"
        )
    return overall


def main():
    parser = argparse.ArgumentParser(
        description="给 config.json 数组元素分配 / 补全 aliasID（幂等）"
    )
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写盘")
    parser.add_argument("--path", help="指定单个 config.json 路径（相对仓库根）")
    parser.add_argument("--namespace", help="搭配 --path 使用，指定命名空间（如 mc）")
    args = parser.parse_args()

    if args.path:
        if not args.namespace:
            parser.error("--path 需要同时指定 --namespace")
        stats = process_config(args.path, args.namespace, dry_run=args.dry_run)
        marker = "[DRY] " if args.dry_run else "[OK]  "
        print(
            f"{marker}{args.namespace:>6}  {args.path}  "
            f"kept={stats['kept']}  new={stats['new']}  "
            f"reassigned={stats['reassigned']}  skipped={stats['skipped']}"
        )
    else:
        process_all(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
