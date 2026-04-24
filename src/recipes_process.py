from tags_zhn_links import get_en2zh_dict

from configs import FINAL_JSON_FILE

from recipes_parser import (
    parse_all,
)

import json
from pathlib import Path

def is_list_has_list(items):
    return any(isinstance(sub_item, list) for sub_item in items)

def not_in_dict(item, en2zh_dict):
    return (
        (item != "null") and 
        (item not in en2zh_dict)
    )

def translate_item(item, en2zh_dict, missing_set):

    """单个 item 翻译（带缺失记录）"""
    if item == "null":
        return "null"

    if item in en2zh_dict:
        return en2zh_dict[item]
    else:
        missing_set.add(item)
        return item  # 保留原值

if __name__ == "__main__":

    en2zh_dict = get_en2zh_dict()

    all_results = parse_all()

    print(f"总配方数量: {len(all_results)}")

    missing_items = set()

    for recipe in all_results:

        # input_items
        recipe["input_items"] = [
            translate_item(item, en2zh_dict, missing_items)
            for item in recipe.get("input_items", [])
        ]

        # output_item
        recipe["output_item"] = translate_item(
            recipe.get("output_item"),
            en2zh_dict,
            missing_items
        )

        # location（有些配方没有）
        if "location" in recipe:
            if is_list_has_list(recipe["location"]):
                print(f"跳过配方: {recipe}")
                continue
                
            recipe["location"] = [
                translate_item(item, en2zh_dict, missing_items)
                for item in recipe["location"]
            ]

    if missing_items:
        print("\n⚠️ 以下物品没有中文映射：")
        for item in sorted(missing_items):
            print(item)   

    with open(FINAL_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已输出到: {FINAL_JSON_FILE}")
