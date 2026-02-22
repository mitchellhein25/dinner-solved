"""
In-memory implementations of all domain repository and port interfaces.
Used exclusively in unit tests — no database or network required.
"""
from dataclasses import dataclass, replace
from typing import Dict, List, Optional
from uuid import UUID

from domain.entities.grocery import GroceryListItem
from domain.entities.household import HouseholdMember
from domain.entities.meal_plan import MealSlot
from domain.entities.preferences import UserPreferences
from domain.entities.recipe import Recipe
from domain.repositories.household_repository import HouseholdRepository
from domain.repositories.meal_plan_repository import (
    MealPlanTemplateRepository,
    WeeklyPlanRepository,
)
from domain.entities.meal_plan import MealPlanTemplate, WeeklyPlan
from domain.repositories.preference_repository import PreferenceRepository
from domain.repositories.recipe_repository import RecipeRepository
from application.ports.ai_port import AIPort, RefinementRequest, SuggestionRequest
from application.ports.export_port import ExportPort


class InMemoryHouseholdRepository(HouseholdRepository):
    def __init__(self, members: Optional[List[HouseholdMember]] = None):
        self._members: List[HouseholdMember] = list(members or [])

    async def get_members(self) -> List[HouseholdMember]:
        return list(self._members)

    async def save_members(self, members: List[HouseholdMember]) -> None:
        self._members = list(members)

    async def get_member(self, member_id: UUID) -> Optional[HouseholdMember]:
        return next((m for m in self._members if m.id == member_id), None)


class InMemoryRecipeRepository(RecipeRepository):
    def __init__(self):
        self._recipes: Dict[UUID, Recipe] = {}

    async def save_recipe(self, recipe: Recipe) -> None:
        self._recipes[recipe.id] = recipe

    async def get_recipes(self) -> List[Recipe]:
        return list(self._recipes.values())

    async def get_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
        return self._recipes.get(recipe_id)

    async def get_favorites(self) -> List[Recipe]:
        return [r for r in self._recipes.values() if r.is_favorite]

    async def toggle_favorite(self, recipe_id: UUID) -> None:
        r = self._recipes.get(recipe_id)
        if r:
            self._recipes[recipe_id] = Recipe(
                id=r.id,
                name=r.name,
                emoji=r.emoji,
                prep_time=r.prep_time,
                ingredients=r.ingredients,
                key_ingredients=r.key_ingredients,
                is_favorite=not r.is_favorite,
                source_url=r.source_url,
            )


class InMemoryMealPlanTemplateRepository(MealPlanTemplateRepository):
    def __init__(self, template: Optional[MealPlanTemplate] = None):
        self._template = template

    async def get_template(self) -> Optional[MealPlanTemplate]:
        return self._template

    async def save_template(self, template: MealPlanTemplate) -> None:
        self._template = template


class InMemoryWeeklyPlanRepository(WeeklyPlanRepository):
    def __init__(self):
        self._plans: Dict[str, WeeklyPlan] = {}

    async def get_plan(self, week_start_date: str) -> Optional[WeeklyPlan]:
        return self._plans.get(week_start_date)

    async def save_plan(self, plan: WeeklyPlan) -> None:
        self._plans[plan.week_start_date] = plan


class InMemoryPreferenceRepository(PreferenceRepository):
    def __init__(self, preferences: Optional[UserPreferences] = None):
        self._preferences = preferences

    async def get_preferences(self) -> Optional[UserPreferences]:
        return self._preferences

    async def save_preferences(self, preferences: UserPreferences) -> None:
        self._preferences = preferences


class FakeAIPort(AIPort):
    """
    Returns fixed recipes regardless of the request.

    suggest_recipes / refine_recipes both return List[List[Recipe]]:
    each recipe in `recipes_to_return` becomes a 3-item inner list
    (the same recipe repeated for simplicity in tests).

    For refine_recipes the fake respects locked_slot_ids, filtering slots
    so the returned list length matches the number of unlocked slots.
    """

    def __init__(self, recipes_to_return: Optional[List[Recipe]] = None):
        self._recipes: List[Recipe] = list(recipes_to_return or [])
        self.last_suggestion_request: Optional[SuggestionRequest] = None
        self.last_refinement_request: Optional[RefinementRequest] = None

    async def suggest_recipes(self, request: SuggestionRequest) -> List[List[Recipe]]:
        self.last_suggestion_request = request
        return [[r, r, r] for r in self._recipes[: len(request.slots)]]

    async def refine_recipes(self, request: RefinementRequest) -> List[List[Recipe]]:
        self.last_refinement_request = request
        unlocked = [
            s for s in request.slots if str(s.id) not in request.locked_slot_ids
        ]
        return [[r, r, r] for r in self._recipes[: len(unlocked)]]


class FakeExportPort(ExportPort):
    def __init__(self, return_value: str = "export://fake"):
        self._return_value = return_value
        self.last_items: Optional[List[GroceryListItem]] = None
        self.last_week: Optional[str] = None

    async def export(self, items: List[GroceryListItem], week_start_date: str) -> str:
        self.last_items = items
        self.last_week = week_start_date
        return self._return_value
