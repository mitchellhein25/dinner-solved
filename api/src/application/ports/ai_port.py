from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from domain.entities.household import HouseholdMember
from domain.entities.meal_plan import MealSlot
from domain.entities.recipe import Recipe


@dataclass
class SuggestionRequest:
    slots: List[MealSlot]
    members: List[HouseholdMember]
    disliked_ingredients: List[str]
    liked_ingredients: List[str]
    cuisine_preferences: List[str]
    week_context: Optional[str] = None
    recent_recipe_names: List[str] = field(default_factory=list)


@dataclass
class RefinementRequest:
    slots: List[MealSlot]
    members: List[HouseholdMember]
    disliked_ingredients: List[str]
    liked_ingredients: List[str]
    cuisine_preferences: List[str]
    existing_assignments: Dict[str, Recipe]  # slot_id (str) -> Recipe
    user_message: str  # e.g. "swap the pasta for something lighter"
    week_context: Optional[str] = None
    locked_slot_ids: List[str] = field(default_factory=list)


class AIPort(ABC):
    @abstractmethod
    async def suggest_recipes(self, request: SuggestionRequest) -> List[List[Recipe]]:
        """Return 3 recipe options for each slot (outer list length == len(slots))."""
        ...

    @abstractmethod
    async def refine_recipes(self, request: RefinementRequest) -> List[List[Recipe]]:
        """Return 3 options for each *unlocked* slot only."""
        ...

    @abstractmethod
    async def generate_instructions(self, recipe: Recipe) -> List[str]:
        """
        Generate step-by-step cooking instructions for the given recipe.
        Called lazily on first detail view; result is cached in the DB.
        """
        ...

    @abstractmethod
    async def parse_recipe_from_url(self, url: str) -> Recipe:
        """
        Fetch a webpage and extract a recipe from it.
        Returns a Recipe domain object (without an id/household — caller assigns those).
        Raises ValueError if no recipe is found on the page.
        """
        ...
