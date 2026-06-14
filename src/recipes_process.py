from id.base import get_english_to_alias_dict

from configs import FINAL_JSON_FILE

from parser.build import (
    parse_all,
)
from tag.refs import is_tag_ref

import json


def is_list_has_list(items):
    return any(isinstance(sub_item, list) for sub_item in items)


def translate_item(item, en2alias_dict, missing_set):
    """单个 item 转为 aliasID（带缺失记录）。tag 引用与 'null' 保持原样。"""
    if item == "null":
        return "null"
    if is_tag_ref(item):
        return item

    if item in en2alias_dict:
        return en2alias_dict[item]
    else:
        missing_set.add(item)
        return item  # 保留原值，避免静默丢失


if __name__ == "__main__":

    en2alias_dict = get_english_to_alias_dict()

    all_results = parse_all()

    print(f"总配方数量: {len(all_results)}")

    missing_items = set()

    for recipe in all_results:

        recipe["input_items"] = [
            translate_item(item, en2alias_dict, missing_items)
            for item in recipe.get("input_items", [])
        ]
        recipe["input_tags"] = recipe.get("input_tags", [])
        recipe["hasTag"] = recipe.get("hasTag", len(recipe["input_tags"]) > 0)

        recipe["output_item"] = translate_item(
            recipe.get("output_item"),
            en2alias_dict,
            missing_items,
        )

        if "location" in recipe:
            if is_list_has_list(recipe["location"]):
                print(f"跳过配方: {recipe}")
                continue

            recipe["location"] = [
                translate_item(item, en2alias_dict, missing_items)
                for item in recipe["location"]
            ]

    if missing_items:
        print("\n[WARN] 以下英文 ID 没有 aliasID 映射，已保留原值：")
        for item in sorted(missing_items):
            print(item)

    with open(FINAL_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 已输出到: {FINAL_JSON_FILE}")
