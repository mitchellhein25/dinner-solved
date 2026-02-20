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
        # Persist each suggested recipe so BuildGroceryList can retrieve them later
        for suggestion in suggestions:
            await self._recipe_repo.save_recipe(suggestion.recipe)

        assignments = [
            SlotAssignment(slot_id=s.slot.id, recipe_id=s.recipe.id)
            for s in suggestions
        ]
        plan = WeeklyPlan(
            id=uuid4(),
            week_start_date=week_start_date,
            assignments=assignments,
        )
        await self._plan_repo.save_plan(plan)
        return plan
