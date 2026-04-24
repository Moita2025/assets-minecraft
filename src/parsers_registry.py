class RecipeParserRegistry:
    def __init__(self):
        self._parsers = {}

    def register(self, recipe_type, parser):
        self._parsers[recipe_type] = parser

    def register_many(self, recipe_types, parser):
        for recipe_type in recipe_types:
            self.register(recipe_type, parser)

    def parse_recipe(self, recipe, tags_list_dict):
        recipe_type = recipe.get("type")
        parser = self._parsers.get(recipe_type)
        if parser is None:
            return []
        return parser(recipe, tags_list_dict)

    def parse_recipes(self, recipes, tags_list_dict):
        results = []
        for recipe in recipes:
            results.extend(self.parse_recipe(recipe, tags_list_dict))
        return results
