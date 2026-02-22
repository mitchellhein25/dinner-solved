"""
In-memory implementations of all domain repository and port interfaces.
Used exclusively in unit tests — no database or network required.
"""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
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

    async def save_recipe(self, recipe: Recipe) -> Recipe:
        # Upsert: match by UUID first, then name
        existing = self._recipes.get(recipe.id)
        if existing is None:
            existing = next(
                (r for r in self._recipes.values() if r.name == recipe.name), None
            )
        if existing is not None:
            updated = replace(
                existing,
                emoji=recipe.emoji,
                prep_time=recipe.prep_time,
                key_ingredients=recipe.key_ingredients,
                ingredients=recipe.ingredients,
                times_used=existing.times_used + 1,
                last_used_at=datetime.now(timezone.utc),
            )
            self._recipes[existing.id] = updated
            return updated
        else:
            new = replace(recipe, times_used=1, last_used_at=datetime.now(timezone.utc))
            self._recipes[new.id] = new
            return new

    async def get_recipes(
        self,
        sort: str = "recent",
        favorites_only: bool = False,
    ) -> List[Recipe]:
        recipes = list(self._recipes.values())
        if favorites_only:
            recipes = [r for r in recipes if r.is_favorite]
        if sort == "most_used":
            recipes.sort(key=lambda r: (-r.times_used, r.name))
        elif sort == "alpha":
            recipes.sort(key=lambda r: r.name)
        elif sort == "favorites_first":
            recipes.sort(key=lambda r: (not r.is_favorite, r.name))
        else:  # recent
            recipes.sort(
                key=lambda r: r.last_used_at or datetime.min, reverse=True
            )
        return recipes

    async def get_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
        return self._recipes.get(recipe_id)

    async def save_instructions(self, recipe_id: UUID, instructions: List[str]) -> None:
        r = self._recipes.get(recipe_id)
        if r is not None:
            self._recipes[recipe_id] = replace(r, cooking_instructions=instructions)

    async def get_recent_recipe_names(self, days: int = 14) -> List[str]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        return [
            r.name for r in self._recipes.values()
            if r.last_used_at is not None and r.last_used_at >= since
        ]

    async def toggle_favorite(self, recipe_id: UUID) -> Optional[Recipe]:
        r = self._recipes.get(recipe_id)
        if r is None:
            return None
        updated = replace(r, is_favorite=not r.is_favorite)
        self._recipes[recipe_id] = updated
        return updated

    async def delete_recipe(self, recipe_id: UUID) -> bool:
        if recipe_id not in self._recipes:
            return False
        del self._recipes[recipe_id]
        return True

    async def update_recipe(self, recipe_id: UUID, name: str, emoji: str) -> Optional[Recipe]:
        r = self._recipes.get(recipe_id)
        if r is None:
            return None
        collision = next(
            (v for k, v in self._recipes.items() if v.name == name and k != recipe_id),
            None,
        )
        if collision is not None:
            raise ValueError(f"A recipe named '{name}' already exists.")
        updated = replace(r, name=name, emoji=emoji)
        self._recipes[recipe_id] = updated
        return updated


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
        self.last_instructions_recipe: Optional[Recipe] = None

    async def suggest_recipes(self, request: SuggestionRequest) -> List[List[Recipe]]:
        self.last_suggestion_request = request
        return [[r, r, r] for r in self._recipes[: len(request.slots)]]

    async def refine_recipes(self, request: RefinementRequest) -> List[List[Recipe]]:
        self.last_refinement_request = request
        unlocked = [
            s for s in request.slots if str(s.id) not in request.locked_slot_ids
        ]
        return [[r, r, r] for r in self._recipes[: len(unlocked)]]

    async def generate_instructions(self, recipe: Recipe) -> List[str]:
        self.last_instructions_recipe = recipe
        return [f"Step 1: Prepare {recipe.name}.", f"Step 2: Cook and serve."]


class FakeExportPort(ExportPort):
    def __init__(self, return_value: str = "export://fake"):
        self._return_value = return_value
        self.last_items: Optional[List[GroceryListItem]] = None
        self.last_week: Optional[str] = None

    async def export(self, items: List[GroceryListItem], week_start_date: str) -> str:
        self.last_items = items
        self.last_week = week_start_date
        return self._return_value
