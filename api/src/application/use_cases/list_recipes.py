from typing import List

from domain.entities.recipe import Recipe
from domain.repositories.recipe_repository import RecipeRepository


class ListRecipesUseCase:
    def __init__(self, recipe_repo: RecipeRepository):
        self._recipe_repo = recipe_repo

    async def execute(
        self,
        sort: str = "recent",
        favorites_only: bool = False,
    ) -> List[Recipe]:
        return await self._recipe_repo.get_recipes(sort=sort, favorites_only=favorites_only)
