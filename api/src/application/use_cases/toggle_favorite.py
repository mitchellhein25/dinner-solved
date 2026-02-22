from typing import Optional
from uuid import UUID

from domain.entities.recipe import Recipe
from domain.repositories.recipe_repository import RecipeRepository


class ToggleFavoriteUseCase:
    def __init__(self, recipe_repo: RecipeRepository):
        self._recipe_repo = recipe_repo

    async def execute(self, recipe_id: UUID) -> Optional[Recipe]:
        return await self._recipe_repo.toggle_favorite(recipe_id)
