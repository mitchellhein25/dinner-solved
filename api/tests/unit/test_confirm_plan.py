import uuid

import pytest

from application.use_cases.confirm_plan import ConfirmPlanUseCase
from application.use_cases.suggest_recipes import RecipeSuggestion
from domain.entities.meal_plan import DayOfWeek, MealSlot, MealType
from domain.entities.recipe import GroceryCategory, Ingredient, Recipe
from tests.unit.fakes import InMemoryRecipeRepository, InMemoryWeeklyPlanRepository


def make_slot() -> MealSlot:
    return MealSlot(
        id=uuid.uuid4(),
        name="Dinner",
        meal_type=MealType.DINNER,
        days=[DayOfWeek.MON],
        member_ids=[uuid.uuid4()],
    )


def make_recipe(name: str = "Pasta") -> Recipe:
    return Recipe(
        id=uuid.uuid4(),
        name=name,
        emoji="🍝",
        prep_time=20,
        ingredients=[Ingredient("Pasta", 2.0, "oz", GroceryCategory.PANTRY)],
        key_ingredients=["pasta"],
    )


@pytest.fixture
def plan_repo():
    return InMemoryWeeklyPlanRepository()


@pytest.fixture
def recipe_repo():
    return InMemoryRecipeRepository()


@pytest.fixture
def use_case(plan_repo, recipe_repo):
    return ConfirmPlanUseCase(plan_repo=plan_repo, recipe_repo=recipe_repo)


class TestConfirmPlan:
    async def test_returns_weekly_plan_with_assignments(self, use_case):
        slot = make_slot()
        recipe = make_recipe()
        suggestions = [RecipeSuggestion(slot=slot, recipe=recipe)]

        plan = await use_case.execute("2026-02-23", suggestions)

        assert plan.week_start_date == "2026-02-23"
        assert len(plan.assignments) == 1
        assert plan.assignments[0].slot_id == slot.id
        assert plan.assignments[0].recipe_id == recipe.id

    async def test_saves_plan_to_repository(self, use_case, plan_repo):
        suggestions = [RecipeSuggestion(slot=make_slot(), recipe=make_recipe())]

        await use_case.execute("2026-02-23", suggestions)

        saved = await plan_repo.get_plan("2026-02-23")
        assert saved is not None

    async def test_persists_all_recipes(self, use_case, recipe_repo):
        r1, r2 = make_recipe("Chicken"), make_recipe("Salmon")
        suggestions = [
            RecipeSuggestion(slot=make_slot(), recipe=r1),
            RecipeSuggestion(slot=make_slot(), recipe=r2),
        ]

        await use_case.execute("2026-02-23", suggestions)

        assert await recipe_repo.get_recipe(r1.id) is not None
        assert await recipe_repo.get_recipe(r2.id) is not None

    async def test_plan_has_unique_id(self, use_case):
        suggestions = [RecipeSuggestion(slot=make_slot(), recipe=make_recipe())]

        plan_a = await use_case.execute("2026-02-23", suggestions)
        plan_b = await use_case.execute("2026-03-02", suggestions)

        assert plan_a.id != plan_b.id

    async def test_empty_suggestions_saves_empty_plan(self, use_case, plan_repo):
        plan = await use_case.execute("2026-02-23", [])

        assert plan.assignments == []
        saved = await plan_repo.get_plan("2026-02-23")
        assert saved is not None
