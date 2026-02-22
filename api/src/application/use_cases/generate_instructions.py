from dataclasses import replace
from typing import Optional
from uuid import UUID

from application.ports.ai_port import AIPort
from domain.entities.recipe import Recipe
from domain.repositories.recipe_repository import RecipeRepository


class GenerateInstructionsUseCase:
    """Generate cooking instructions for a recipe that has none yet.

    This is intentionally separate from GetRecipeUseCase so that the detail
    page can load instantly and then call this endpoint in the background.
    """

    def __init__(self, recipe_repo: RecipeRepository, ai_port: AIPort):
        self._recipe_repo = recipe_repo
        self._ai_port = ai_port

    async def execute(self, recipe_id: UUID) -> Optional[Recipe]:
        recipe = await self._recipe_repo.get_recipe(recipe_id)
        if recipe is None:
            return None

        if recipe.cooking_instructions is None:
            instructions = await self._ai_port.generate_instructions(recipe)
            await self._recipe_repo.save_instructions(recipe.id, instructions)
            recipe = replace(recipe, cooking_instructions=instructions)

        return recipe
