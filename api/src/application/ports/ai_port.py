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
