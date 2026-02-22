from typing import List, Optional
from uuid import UUID

from domain.entities.recipe import Ingredient, Recipe
from domain.repositories.recipe_repository import RecipeRepository


class FullUpdateRecipeUseCase:
    """Update all editable fields of an existing recipe."""

    def __init__(self, recipe_repo: RecipeRepository):
        self._recipe_repo = recipe_repo

    async def execute(
        self,
        recipe_id: UUID,
        name: str,
        emoji: str,
        prep_time: int,
        key_ingredients: List[str],
        ingredients: List[Ingredient],
        source_url: Optional[str],
        cooking_instructions: Optional[List[str]],
    ) -> Optional[Recipe]:
        """
        Returns updated recipe, None if not found.
        Raises ValueError on name collision.
        """
        return await self._recipe_repo.full_update_recipe(
            recipe_id=recipe_id,
            name=name,
            emoji=emoji,
            prep_time=prep_time,
            key_ingredients=key_ingredients,
            ingredients=ingredients,
            source_url=source_url,
            cooking_instructions=cooking_instructions,
        )
