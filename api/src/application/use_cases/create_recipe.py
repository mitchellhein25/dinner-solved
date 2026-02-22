from domain.entities.recipe import Recipe
from domain.repositories.recipe_repository import RecipeRepository


class CreateRecipeUseCase:
    """Persist a new user-added recipe (manual entry or confirmed URL import)."""

    def __init__(self, recipe_repo: RecipeRepository):
        self._recipe_repo = recipe_repo

    async def execute(self, recipe: Recipe) -> Recipe:
        """
        Saves the recipe with times_used=0.
        Raises ValueError on name collision.
        """
        return await self._recipe_repo.create_recipe(recipe)
