from typing import List
from uuid import uuid4

from domain.entities.meal_plan import SlotAssignment, WeeklyPlan
from domain.repositories.meal_plan_repository import WeeklyPlanRepository
from domain.repositories.recipe_repository import RecipeRepository
from application.use_cases.suggest_recipes import RecipeSuggestion


class ConfirmPlanUseCase:
    def __init__(
        self,
        plan_repo: WeeklyPlanRepository,
        recipe_repo: RecipeRepository,
    ):
        self._plan_repo = plan_repo
        self._recipe_repo = recipe_repo

    async def execute(
        self,
        week_start_date: str,
        suggestions: List[RecipeSuggestion],
    ) -> WeeklyPlan:
        # Upsert each recipe; save_recipe returns the canonical entity (may have a
        # different id if matched by name rather than UUID).
        saved = [
            (s.slot, await self._recipe_repo.save_recipe(s.recipe))
            for s in suggestions
        ]

        assignments = [
            SlotAssignment(slot_id=slot.id, recipe_id=recipe.id)
            for slot, recipe in saved
        ]
        plan = WeeklyPlan(
            id=uuid4(),
            week_start_date=week_start_date,
            assignments=assignments,
        )
        await self._plan_repo.save_plan(plan)
        return plan
