import uuid

import pytest

from application.use_cases.build_grocery_list import BuildGroceryListUseCase
from domain.entities.grocery import GroceryListItem
from domain.entities.household import HouseholdMember
from domain.entities.meal_plan import (
    DayOfWeek,
    MealPlanTemplate,
    MealSlot,
    MealType,
    SlotAssignment,
    WeeklyPlan,
)
from domain.entities.recipe import GroceryCategory, Ingredient, Recipe
from domain.services.grocery_list_service import GroceryListService
from domain.services.serving_calculator import ServingCalculator
from tests.unit.fakes import (
    InMemoryHouseholdRepository,
    InMemoryMealPlanTemplateRepository,
    InMemoryRecipeRepository,
    InMemoryWeeklyPlanRepository,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_member(serving_size: float = 1.0) -> HouseholdMember:
    return HouseholdMember(id=uuid.uuid4(), name="Test", emoji="🧑", serving_size=serving_size)


def make_slot(member_ids: list) -> MealSlot:
    return MealSlot(
        id=uuid.uuid4(),
        name="Dinner",
        meal_type=MealType.DINNER,
        days=[DayOfWeek.MON],
        member_ids=member_ids,
    )


def make_recipe(*ingredients: Ingredient, name: str = "Recipe") -> Recipe:
    return Recipe(
        id=uuid.uuid4(),
        name=name,
        emoji="🍽️",
        prep_time=30,
        ingredients=list(ingredients),
        key_ingredients=[],
    )


def make_plan(assignments: list, week: str = "2026-02-23") -> WeeklyPlan:
    return WeeklyPlan(id=uuid.uuid4(), week_start_date=week, assignments=assignments)


def build_use_case(
    plan=None,
    template=None,
    members=None,
    recipes=None,
) -> BuildGroceryListUseCase:
    plan_repo = InMemoryWeeklyPlanRepository()
    if plan:
        import asyncio
        asyncio.get_event_loop().run_until_complete(plan_repo.save_plan(plan))

    recipe_repo = InMemoryRecipeRepository()
    if recipes:
        for r in recipes:
            asyncio.get_event_loop().run_until_complete(recipe_repo.save_recipe(r))

    return BuildGroceryListUseCase(
        plan_repo=plan_repo,
        template_repo=InMemoryMealPlanTemplateRepository(template=template),
        household_repo=InMemoryHouseholdRepository(members=members or []),
        recipe_repo=recipe_repo,
        grocery_service=GroceryListService(ServingCalculator()),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBuildGroceryList:
    async def test_raises_when_no_plan_for_week(self):
        use_case = BuildGroceryListUseCase(
            plan_repo=InMemoryWeeklyPlanRepository(),
            template_repo=InMemoryMealPlanTemplateRepository(),
            household_repo=InMemoryHouseholdRepository(),
            recipe_repo=InMemoryRecipeRepository(),
            grocery_service=GroceryListService(ServingCalculator()),
        )

        with pytest.raises(ValueError, match="2026-02-23"):
            await use_case.execute("2026-02-23")

    async def test_returns_grocery_list_for_confirmed_plan(self):
        member = make_member(1.0)
        slot = make_slot([member.id])
        recipe = make_recipe(
            Ingredient("Chicken", 0.5, "lbs", GroceryCategory.MEAT),
            name="Grilled Chicken",
        )
        template = MealPlanTemplate(id=uuid.uuid4(), slots=[slot])
        assignment = SlotAssignment(slot_id=slot.id, recipe_id=recipe.id)
        plan = make_plan([assignment])

        plan_repo = InMemoryWeeklyPlanRepository()
        recipe_repo = InMemoryRecipeRepository()
        await plan_repo.save_plan(plan)
        await recipe_repo.save_recipe(recipe)

        use_case = BuildGroceryListUseCase(
            plan_repo=plan_repo,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(members=[member]),
            recipe_repo=recipe_repo,
            grocery_service=GroceryListService(ServingCalculator()),
        )

        result = await use_case.execute("2026-02-23")

        assert len(result) == 1
        assert result[0].name == "Chicken"
        assert result[0].quantity == 0.5  # 0.5 * 1 serving * 1 day

    async def test_ingredients_scaled_for_household(self):
        m1 = make_member(1.5)
        m2 = make_member(1.0)
        slot = make_slot([m1.id, m2.id])  # 2.5 servings × 1 day = 2.5 total
        recipe = make_recipe(
            Ingredient("Rice", 1.0, "cups", GroceryCategory.PANTRY),
            name="Rice Bowl",
        )
        template = MealPlanTemplate(id=uuid.uuid4(), slots=[slot])
        plan = make_plan([SlotAssignment(slot_id=slot.id, recipe_id=recipe.id)])

        plan_repo = InMemoryWeeklyPlanRepository()
        recipe_repo = InMemoryRecipeRepository()
        await plan_repo.save_plan(plan)
        await recipe_repo.save_recipe(recipe)

        use_case = BuildGroceryListUseCase(
            plan_repo=plan_repo,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(members=[m1, m2]),
            recipe_repo=recipe_repo,
            grocery_service=GroceryListService(ServingCalculator()),
        )

        result = await use_case.execute("2026-02-23")

        assert result[0].quantity == 2.5

    async def test_returns_list_type(self):
        plan_repo = InMemoryWeeklyPlanRepository()
        empty_plan = make_plan([])
        await plan_repo.save_plan(empty_plan)

        use_case = BuildGroceryListUseCase(
            plan_repo=plan_repo,
            template_repo=InMemoryMealPlanTemplateRepository(
                template=MealPlanTemplate(id=uuid.uuid4(), slots=[])
            ),
            household_repo=InMemoryHouseholdRepository(),
            recipe_repo=InMemoryRecipeRepository(),
            grocery_service=GroceryListService(ServingCalculator()),
        )

        result = await use_case.execute("2026-02-23")

        assert isinstance(result, list)
