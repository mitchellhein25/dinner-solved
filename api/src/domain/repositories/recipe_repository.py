from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.recipe import Recipe


class RecipeRepository(ABC):
    @abstractmethod
    async def save_recipe(self, recipe: Recipe) -> Recipe:
        """
        Upsert a recipe. Matches on UUID first, then falls back to name.
        Increments times_used and updates last_used_at on match.
        Returns the canonical Recipe (may have a different id if matched by name).
        """
        ...

    @abstractmethod
    async def get_recipes(
        self,
        sort: str = "recent",
        favorites_only: bool = False,
    ) -> List[Recipe]:
        """
        List all household recipes.
        sort: "recent" | "most_used" | "alpha" | "favorites_first"
        """
        ...

    @abstractmethod
    async def get_recipe(self, recipe_id: UUID) -> Optional[Recipe]: ...

    @abstractmethod
    async def save_instructions(self, recipe_id: UUID, instructions: List[str]) -> None:
        """Persist lazily-generated cooking instructions for an existing recipe."""
        ...

    @abstractmethod
    async def toggle_favorite(self, recipe_id: UUID) -> Optional[Recipe]:
        """Toggle is_favorite. Returns the updated recipe, or None if not found."""
        ...

    @abstractmethod
    async def get_recent_recipe_names(self, days: int = 14) -> List[str]:
        """Return names of recipes confirmed within the last `days` days, newest first."""
        ...

    @abstractmethod
    async def delete_recipe(self, recipe_id: UUID) -> bool:
        """Soft-delete a recipe. Returns True if found and deleted, False if not found."""
        ...

    @abstractmethod
    async def update_recipe(self, recipe_id: UUID, name: str, emoji: str) -> Optional[Recipe]:
        """Update a recipe's name and emoji. Returns updated recipe, None if not found.
        Raises ValueError if the new name already exists on another recipe in this household.
        """
        ...
