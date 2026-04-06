from recipes_analysis import get_original_recipes
from tags_zhn_links import get_tags_list_dict
from configs import ANALYSIS_PATH

import itertools

def parse_crafting_shaped(tags_list_dict, original_recipes):

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
                symbol_map[symbol] = tags_list_dict.get(value, [])

            else:
                symbol_map[symbol] = [value]

        # print(symbol_map)

        # 👉 2. 处理 pattern → 3x3
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

if __name__ == "__main__":

    tags_list_dict = get_tags_list_dict()
    original_recipes = get_original_recipes()

    print(len(parse_crafting_shaped(tags_list_dict, original_recipes)))

    pass