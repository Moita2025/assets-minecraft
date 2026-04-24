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


def collect_items_and_tags(values):
    item_set = set()
    tag_set = set()
    for value in values:
        if isinstance(value, str):
            if is_tag_ref(value):
                tag_set.add(value)
            elif value != "null":
                item_set.add(value)
    return sorted(item_set), sorted(tag_set)


def pick_display_value(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                return item
    return "null"


def has_tag_in_value(value):
    if is_tag_ref(value):
        return True
    if isinstance(value, list):
        return any(is_tag_ref(item) for item in value)
    return False


def has_tag_in_values(values):
    return any(has_tag_in_value(value) for value in values)


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

    has_tag = has_tag_in_values(key.values())
    symbol_map = {}
    raw_symbol_map = {}
    for symbol, value in key.items():
        raw_symbol_map[symbol] = value
        if is_tag_ref(value):
            symbol_map[symbol] = get_tag_items(value, tags_list_dict)
        elif isinstance(value, list):
            symbol_map[symbol] = [item for item in value]
        else:
            symbol_map[symbol] = [value]

    flat_pattern, symbol_keys, symbol_lists = parse_pattern(
        pattern, raw_symbol_map if has_tag else symbol_map
    )

    if has_tag:
        replace_map = {}
        for symbol in symbol_keys:
            replace_map[symbol] = pick_display_value(raw_symbol_map.get(symbol))

        location = []
        raw_inputs = []
        for c in flat_pattern:
            if c == " ":
                location.append("null")
            else:
                item = replace_map[c]
                location.append(item)
                raw_inputs.append(item)

        input_items, input_tags = collect_items_and_tags(raw_inputs)
        return [
            {
                "type": "minecraft:crafting_shaped",
                "hasTag": True,
                "input_items": input_items,
                "input_tags": input_tags,
                "output_item": result.get("id"),
                "output_count": result.get("count", 1),
                "location": location,
            }
        ]

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
                "hasTag": False,
                "input_items": list(set(map(str, input_items))),
                "input_tags": [],
                "output_item": result.get("id"),
                "output_count": result.get("count", 1),
                "location": location,
            }
        )

    return parsed_results


def parse_crafting_shapeless_recipe(recipe, tags_list_dict):
    ingredients = recipe.get("ingredients", [])
    result = recipe.get("result", {})
    has_tag = has_tag_in_values(ingredients)
    parsed_ingredients = parse_ingredients(ingredients, tags_list_dict)

    if has_tag:
        display_items = [pick_display_value(ing) for ing in ingredients]
        location = build_shapeless_location(display_items)
        input_items, input_tags = collect_items_and_tags(display_items)
        return [
            {
                "type": "minecraft:crafting_shapeless",
                "hasTag": True,
                "input_items": input_items,
                "input_tags": input_tags,
                "output_item": result.get("id"),
                "output_count": result.get("count", 1),
                "location": location,
            }
        ]

    parsed_results = []
    for combo in itertools.product(*parsed_ingredients):
        items = list(combo)
        location = build_shapeless_location(items)
        parsed_results.append(
            {
                "type": "minecraft:crafting_shapeless",
                "hasTag": False,
                "input_items": list(set(map(str, items))),
                "input_tags": [],
                "output_item": result.get("id"),
                "output_count": result.get("count", 1),
                "location": location,
            }
        )

    return parsed_results


def parse_single_ingredient_recipe(recipe, tags_list_dict):
    ingredient = recipe.get("ingredient")
    result = recipe.get("result", {})
    has_tag = has_tag_in_value(ingredient)
    if has_tag:
        display_item = pick_display_value(ingredient)
        input_items, input_tags = collect_items_and_tags([display_item])
        return [
            {
                "type": recipe.get("type"),
                "hasTag": True,
                "input_items": input_items,
                "input_tags": input_tags,
                "output_item": result.get("id") if isinstance(result, dict) else result,
                "output_count": result.get("count", 1) if isinstance(result, dict) else 1,
            }
        ]

    parsed_ingredients = parse_ingredients([ingredient], tags_list_dict)

    parsed_results = []
    for combo in itertools.product(*parsed_ingredients):
        item = combo[0] if combo else "null"
        parsed_results.append(
            {
                "type": recipe.get("type"),
                "hasTag": False,
                "input_items": [str(item)],
                "input_tags": [],
                "output_item": result.get("id") if isinstance(result, dict) else result,
                "output_count": result.get("count", 1) if isinstance(result, dict) else 1,
            }
        )

    return parsed_results
