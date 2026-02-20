from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.recipe import Recipe


class RecipeRepository(ABC):
    @abstractmethod
    async def save_recipe(self, recipe: Recipe) -> None: ...

    @abstractmethod
    async def get_recipes(self) -> List[Recipe]: ...

    @abstractmethod
    async def get_recipe(self, recipe_id: UUID) -> Optional[Recipe]: ...

    @abstractmethod
    async def get_favorites(self) -> List[Recipe]: ...

    @abstractmethod
    async def toggle_favorite(self, recipe_id: UUID) -> None: ...
