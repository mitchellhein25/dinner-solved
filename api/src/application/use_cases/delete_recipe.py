from uuid import UUID

from domain.repositories.recipe_repository import RecipeRepository


class DeleteRecipeUseCase:
    def __init__(self, recipe_repo: RecipeRepository):
        self._recipe_repo = recipe_repo

    async def execute(self, recipe_id: UUID) -> bool:
        """Soft-delete a recipe. Returns True if found, False if not found."""
        return await self._recipe_repo.delete_recipe(recipe_id)
