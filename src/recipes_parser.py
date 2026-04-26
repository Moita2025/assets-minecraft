from recipe.base import get_original_recipes
from tags_zhn_links import get_tags_list_dict
from parser.registry import RecipeParserRegistry
from parsers_minecraft import (
    parse_crafting_shaped_recipe,
    parse_crafting_shapeless_recipe,
    parse_single_ingredient_recipe,
)

TAGS_LIST_DICT = get_tags_list_dict()
ORIGINAL_RECIPES = get_original_recipes()

OTHER_RECIPE_TYPES = {
    "minecraft:smelting",
    "minecraft:blasting",
    "minecraft:smoking",
    "minecraft:campfire_cooking",
    "minecraft:stonecutting",
}


def build_registry():
    registry = RecipeParserRegistry()
    registry.register("minecraft:crafting_shaped", parse_crafting_shaped_recipe)
    registry.register("minecraft:crafting_shapeless", parse_crafting_shapeless_recipe)
    registry.register_many(OTHER_RECIPE_TYPES, parse_single_ingredient_recipe)
    return registry


def parse_by_types(target_types, tags_list_dict=TAGS_LIST_DICT, original_recipes=ORIGINAL_RECIPES):
    registry = build_registry()
    filtered_recipes = [r for r in original_recipes if r.get("type") in target_types]
    return registry.parse_recipes(filtered_recipes, tags_list_dict)


def parse_crafting_shaped(tags_list_dict=TAGS_LIST_DICT, original_recipes=ORIGINAL_RECIPES):
    return parse_by_types({"minecraft:crafting_shaped"}, tags_list_dict, original_recipes)


def parse_crafting_shapeless(tags_list_dict=TAGS_LIST_DICT, original_recipes=ORIGINAL_RECIPES):
    return parse_by_types({"minecraft:crafting_shapeless"}, tags_list_dict, original_recipes)


def parse_other(tags_list_dict=TAGS_LIST_DICT, original_recipes=ORIGINAL_RECIPES):
    return parse_by_types(OTHER_RECIPE_TYPES, tags_list_dict, original_recipes)


def parse_all(tags_list_dict=TAGS_LIST_DICT, original_recipes=ORIGINAL_RECIPES):
    registry = build_registry()
    return registry.parse_recipes(original_recipes, tags_list_dict)

if __name__ == "__main__":

    print(parse_crafting_shaped()[0:10])
    print(parse_crafting_shapeless()[0:10])
    print(parse_other()[0:10])

    pass