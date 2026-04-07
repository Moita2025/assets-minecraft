from recipes_analysis import get_original_recipes
from tags_zhn_links import get_tags_list_dict
from configs import ANALYSIS_PATH

import itertools

TAGS_LIST_DICT = get_tags_list_dict()
ORIGINAL_RECIPES = get_original_recipes()

def parse_pattern(pattern, symbol_map):
    grid = []

    for row in pattern:
        row = list(row)
        while len(row) < 3:
            row.append(" ")
        grid.append(row)

    while len(grid) < 3:
        grid.insert(0, [" ", " ", " "])

    flat_pattern = [c for row in grid for c in row]

    # 👉 3. 找到所有用到的 symbol
    used_symbols = set([c for c in flat_pattern if c != " "])

    # 👉 4. 准备组合
    symbol_lists = []
    symbol_keys = []

    for sym in used_symbols:
        items = symbol_map.get(sym, [])
        if not items:
            items = ["null"]
        symbol_lists.append(items)
        symbol_keys.append(sym)

    return flat_pattern, symbol_keys, symbol_lists

def parse_crafting_shaped(tags_list_dict = TAGS_LIST_DICT, original_recipes = ORIGINAL_RECIPES):

    results = []

    for recipe in original_recipes:

        if recipe.get("type") != "minecraft:crafting_shaped":
            continue

        pattern = recipe.get("pattern", [])
        key = recipe.get("key", {})
        result = recipe.get("result", {})

        # 👉 1. 构建 symbol -> item列表（已扁平化）
        symbol_map = {}

        for symbol, value in key.items():

            if isinstance(value, str) and value.startswith("#minecraft:"):
                symbol_map[symbol] = tags_list_dict.get(value.replace("#minecraft:",""), [])

            elif isinstance(value, list):
                symbol_map[symbol] = [item for item in value]

            else:
                symbol_map[symbol] = [value]

        # print(symbol_map)

        flat_pattern, symbol_keys, symbol_lists = parse_pattern(pattern, symbol_map)

        # 👉 5. 笛卡尔积生成所有组合
        for combination in itertools.product(*symbol_lists):

            replace_map = dict(zip(symbol_keys, combination))

            location = []
            input_items = []

            for c in flat_pattern:
                if c == " ":
                    location.append("null")
                else:
                    item = replace_map[c]
                    location.append(item)
                    input_items.append(item)

            parsed = {
                "type": "minecraft:crafting_shaped",
                "input_items": list(set(map(str, input_items))),
                "output_item": result.get("id"),
                "output_count": result.get("count", 1),
                "location": location
            }

            results.append(parsed)

    return results

POSITION_MAP = {
    1: [5],
    2: [5, 8],
    3: [4, 5, 6],
    4: [4, 5, 7, 8],
    5: [4, 5, 7, 8, 9],
    6: [4, 5, 6, 7, 8, 9],
    7: [2, 4, 5, 6, 7, 8, 9],
    8: [1, 2, 4, 5, 6, 7, 8, 9],
    9: [1, 2, 3, 4, 5, 6, 7, 8, 9],
}

def build_shapeless_location(items):
    count = len(items)

    positions = POSITION_MAP.get(count, [])
    
    # 初始化9格
    location = ["null"] * 9

    for item, pos in zip(items, positions):
        location[pos - 1] = item  # 转成0-based index

    return location

def parse_ingredients(ingredients, tags_list_dict):
    result = []

    for ing in ingredients:

        # 👉 情况1：字符串
        if isinstance(ing, str):

            if ing.startswith("#minecraft:"):
                result.append(tags_list_dict.get(ing, []))
            else:
                result.append([ing])

        # 👉 情况2：列表（多个候选）
        elif isinstance(ing, list):

            candidates = []

            for item in ing:
                if isinstance(item, str) and item.startswith("#minecraft:"):
                    candidates.extend(tags_list_dict.get(item, []))
                else:
                    candidates.append(item)

            result.append(candidates)

        else:
            # 👉 兜底（防炸）
            result.append([])

    return result

def parse_crafting_shapeless(tags_list_dict = TAGS_LIST_DICT, original_recipes = ORIGINAL_RECIPES):

    results = []

    for recipe in original_recipes:

        if recipe.get("type") != "minecraft:crafting_shapeless":
            continue

        ingredients = recipe.get("ingredients", [])
        result = recipe.get("result", {})

        parsed_ingredients = parse_ingredients(ingredients, tags_list_dict)

        # 👉 笛卡尔积（展开 tag）
        for combo in itertools.product(*parsed_ingredients):

            items = list(combo)

            location = build_shapeless_location(items)

            results.append({
                "type": "minecraft:crafting_shapeless",
                "input_items": list(set(map(str, items))),
                "output_item": result.get("id"),
                "output_count": result.get("count", 1),
                "location": location
            })

    return results

def parse_other(tags_list_dict = TAGS_LIST_DICT, original_recipes = ORIGINAL_RECIPES):

    results = []

    TARGET_TYPES = {
        "minecraft:smelting",
        "minecraft:blasting",
        "minecraft:smoking",
        "minecraft:campfire_cooking",
        "minecraft:stonecutting"
    }

    for recipe in original_recipes:

        r_type = recipe.get("type")

        if r_type not in TARGET_TYPES:
            continue

        ingredient = recipe.get("ingredient")
        result = recipe.get("result", {})

        # 👉 解析 ingredient（复用逻辑）
        parsed_ingredients = parse_ingredients([ingredient], tags_list_dict)

        # 👉 展开 tag（笛卡尔积）
        for combo in itertools.product(*parsed_ingredients):

            item = combo[0] if combo else "null"

            results.append({
                "type": r_type,
                "input_items": [str(item)],   # 单元素列表
                "output_item": result.get("id") if isinstance(result, dict) else result,
                "output_count": result.get("count", 1) if isinstance(result, dict) else 1
            })

    return results

if __name__ == "__main__":

    print(parse_crafting_shaped()[0:10])
    print(parse_crafting_shapeless()[0:10])
    print(parse_other()[0:10])

    pass