from typing import Optional
from uuid import UUID

from domain.entities.recipe import Recipe
from domain.repositories.recipe_repository import RecipeRepository


class GetRecipeUseCase:
    """Fetch a recipe by ID. Returns immediately — cooking_instructions may be None.
    Call GenerateInstructionsUseCase separately to lazily generate instructions.
    """

    def __init__(self, recipe_repo: RecipeRepository):
        self._recipe_repo = recipe_repo

    async def execute(self, recipe_id: UUID) -> Optional[Recipe]:
        return await self._recipe_repo.get_recipe(recipe_id)
