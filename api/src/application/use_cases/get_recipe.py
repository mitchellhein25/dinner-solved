from typing import Optional
from uuid import UUID

from application.ports.ai_port import AIPort
from domain.entities.recipe import Recipe
from domain.repositories.recipe_repository import RecipeRepository


class GetRecipeUseCase:
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
            # Return a copy with instructions populated (avoids a second DB fetch)
            from dataclasses import replace
            recipe = replace(recipe, cooking_instructions=instructions)

        return recipe
