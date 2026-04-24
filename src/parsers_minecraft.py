import itertools

from refs import is_tag_ref, normalize_tag_ref


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


def get_tag_items(tag_ref, tags_list_dict):
    normalized_tag = normalize_tag_ref(tag_ref)
    if not normalized_tag:
        return []
    return tags_list_dict.get(normalized_tag, [])


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
    used_symbols = set([c for c in flat_pattern if c != " "])

    symbol_lists = []
    symbol_keys = []
    for sym in used_symbols:
        items = symbol_map.get(sym, [])
        if not items:
            items = ["null"]
        symbol_lists.append(items)
        symbol_keys.append(sym)

    return flat_pattern, symbol_keys, symbol_lists


def build_shapeless_location(items):
    count = len(items)
    positions = POSITION_MAP.get(count, [])
    location = ["null"] * 9
    for item, pos in zip(items, positions):
        location[pos - 1] = item
    return location


def parse_ingredients(ingredients, tags_list_dict):
    result = []
    for ing in ingredients:
        if isinstance(ing, str):
            if is_tag_ref(ing):
                result.append(get_tag_items(ing, tags_list_dict))
            else:
                result.append([ing])
        elif isinstance(ing, list):
            candidates = []
            for item in ing:
                if is_tag_ref(item):
                    candidates.extend(get_tag_items(item, tags_list_dict))
                else:
                    candidates.append(item)
            result.append(candidates)
        else:
            result.append([])
    return result


def parse_crafting_shaped_recipe(recipe, tags_list_dict):
    pattern = recipe.get("pattern", [])
    key = recipe.get("key", {})
    result = recipe.get("result", {})

    symbol_map = {}
    for symbol, value in key.items():
        if is_tag_ref(value):
            symbol_map[symbol] = get_tag_items(value, tags_list_dict)
        elif isinstance(value, list):
            symbol_map[symbol] = [item for item in value]
        else:
            symbol_map[symbol] = [value]

    flat_pattern, symbol_keys, symbol_lists = parse_pattern(pattern, symbol_map)

    parsed_results = []
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

        parsed_results.append(
            {
                "type": "minecraft:crafting_shaped",
                "input_items": list(set(map(str, input_items))),
                "output_item": result.get("id"),
                "output_count": result.get("count", 1),
                "location": location,
            }
        )

    return parsed_results


def parse_crafting_shapeless_recipe(recipe, tags_list_dict):
    ingredients = recipe.get("ingredients", [])
    result = recipe.get("result", {})
    parsed_ingredients = parse_ingredients(ingredients, tags_list_dict)

    parsed_results = []
    for combo in itertools.product(*parsed_ingredients):
        items = list(combo)
        location = build_shapeless_location(items)
        parsed_results.append(
            {
                "type": "minecraft:crafting_shapeless",
                "input_items": list(set(map(str, items))),
                "output_item": result.get("id"),
                "output_count": result.get("count", 1),
                "location": location,
            }
        )

    return parsed_results


def parse_single_ingredient_recipe(recipe, tags_list_dict):
    ingredient = recipe.get("ingredient")
    result = recipe.get("result", {})
    parsed_ingredients = parse_ingredients([ingredient], tags_list_dict)

    parsed_results = []
    for combo in itertools.product(*parsed_ingredients):
        item = combo[0] if combo else "null"
        parsed_results.append(
            {
                "type": recipe.get("type"),
                "input_items": [str(item)],
                "output_item": result.get("id") if isinstance(result, dict) else result,
                "output_count": result.get("count", 1) if isinstance(result, dict) else 1,
            }
        )

    return parsed_results
