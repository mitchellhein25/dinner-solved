from typing import Optional
from uuid import UUID

from domain.entities.recipe import Recipe
from domain.repositories.recipe_repository import RecipeRepository


class UpdateRecipeUseCase:
    def __init__(self, recipe_repo: RecipeRepository):
        self._recipe_repo = recipe_repo

    async def execute(self, recipe_id: UUID, name: str, emoji: str) -> Optional[Recipe]:
        """Update a recipe's name and emoji.
        Returns updated recipe, None if not found.
        Raises ValueError on name collision.
        """
        return await self._recipe_repo.update_recipe(recipe_id, name, emoji)
