from typing import Dict, List
from uuid import UUID

from domain.entities.grocery import GroceryListItem
from domain.entities.recipe import Recipe
from domain.repositories.household_repository import HouseholdRepository
from domain.repositories.meal_plan_repository import (
    MealPlanTemplateRepository,
    WeeklyPlanRepository,
)
from domain.repositories.recipe_repository import RecipeRepository
from domain.services.grocery_list_service import GroceryListService


class BuildGroceryListUseCase:
    def __init__(
        self,
        plan_repo: WeeklyPlanRepository,
        template_repo: MealPlanTemplateRepository,
        household_repo: HouseholdRepository,
        recipe_repo: RecipeRepository,
        grocery_service: GroceryListService,
    ):
        self._plan_repo = plan_repo
        self._template_repo = template_repo
        self._household_repo = household_repo
        self._recipe_repo = recipe_repo
        self._grocery_service = grocery_service

    async def execute(self, week_start_date: str) -> List[GroceryListItem]:
        plan = await self._plan_repo.get_plan(week_start_date)
        if plan is None:
            raise ValueError(f"No confirmed plan found for week '{week_start_date}'.")

        template = await self._template_repo.get_template()
        members = await self._household_repo.get_members()

        recipes: Dict[str, Recipe] = {}
        for assignment in plan.assignments:
            recipe = await self._recipe_repo.get_recipe(assignment.recipe_id)
            if recipe:
                recipes[str(assignment.recipe_id)] = recipe

        return self._grocery_service.build(
            weekly_plan=plan,
            slots=template.slots,
            members=members,
            recipes=recipes,
        )
