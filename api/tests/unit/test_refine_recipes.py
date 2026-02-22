"""Unit tests for RefineRecipesUseCase."""
import uuid

import pytest

from application.use_cases.refine_recipes import RefineRecipesUseCase
from application.use_cases.suggest_recipes import SlotOptions
from domain.entities.household import HouseholdMember
from domain.entities.meal_plan import DayOfWeek, MealPlanTemplate, MealSlot, MealType
from domain.entities.preferences import UserPreferences
from domain.entities.recipe import GroceryCategory, Ingredient, Recipe
from tests.unit.fakes import (
    FakeAIPort,
    InMemoryHouseholdRepository,
    InMemoryMealPlanTemplateRepository,
    InMemoryPreferenceRepository,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_slot(name: str = "Dinner") -> MealSlot:
    return MealSlot(
        id=uuid.uuid4(),
        name=name,
        meal_type=MealType.DINNER,
        days=[DayOfWeek.MON, DayOfWeek.TUE],
        member_ids=[],
    )


def make_recipe(name: str = "Pasta") -> Recipe:
    return Recipe(
        id=uuid.uuid4(),
        name=name,
        emoji="🍝",
        prep_time=30,
        ingredients=[Ingredient("Pasta", 2.0, "oz", GroceryCategory.PANTRY)],
        key_ingredients=["pasta"],
    )


def make_template(n_slots: int = 2) -> MealPlanTemplate:
    return MealPlanTemplate(
        id=uuid.uuid4(),
        slots=[make_slot(f"Slot {i}") for i in range(n_slots)],
    )


def build_use_case(template=None, recipes_to_return=None) -> RefineRecipesUseCase:
    return RefineRecipesUseCase(
        ai_adapter=FakeAIPort(recipes_to_return=recipes_to_return or []),
        template_repo=InMemoryMealPlanTemplateRepository(template=template),
        household_repo=InMemoryHouseholdRepository(),
        preference_repo=InMemoryPreferenceRepository(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRefineRecipes:
    async def test_returns_slot_options_for_all_slots_when_none_locked(self):
        template = make_template(n_slots=3)
        recipes = [make_recipe(f"Recipe {i}") for i in range(3)]
        use_case = build_use_case(template=template, recipes_to_return=recipes)

        result = await use_case.execute(
            existing_assignments={},
            user_message="make it lighter",
        )

        assert len(result) == 3
        assert all(isinstance(r, SlotOptions) for r in result)

    async def test_each_slot_options_has_three_choices(self):
        template = make_template(2)
        use_case = build_use_case(
            template=template,
            recipes_to_return=[make_recipe("A"), make_recipe("B")],
        )

        result = await use_case.execute(
            existing_assignments={},
            user_message="something quick",
        )

        assert all(len(r.options) == 3 for r in result)

    async def test_locked_slots_are_excluded_from_result(self):
        template = make_template(n_slots=3)
        locked_slot = template.slots[1]
        recipes = [make_recipe(f"R{i}") for i in range(2)]  # only 2 unlocked
        use_case = build_use_case(template=template, recipes_to_return=recipes)

        result = await use_case.execute(
            existing_assignments={},
            user_message="swap something",
            locked_slot_ids=[str(locked_slot.id)],
        )

        assert len(result) == 2
        returned_slot_ids = {str(r.slot.id) for r in result}
        assert str(locked_slot.id) not in returned_slot_ids

    async def test_all_locked_returns_empty(self):
        template = make_template(2)
        locked_ids = [str(s.id) for s in template.slots]
        use_case = build_use_case(template=template, recipes_to_return=[])

        result = await use_case.execute(
            existing_assignments={},
            user_message="no-op",
            locked_slot_ids=locked_ids,
        )

        assert result == []

    async def test_passes_locked_slot_ids_to_ai(self):
        template = make_template(2)
        locked_slot = template.slots[0]
        ai = FakeAIPort(recipes_to_return=[make_recipe()])
        use_case = RefineRecipesUseCase(
            ai_adapter=ai,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(),
            preference_repo=InMemoryPreferenceRepository(),
        )

        await use_case.execute(
            existing_assignments={},
            user_message="lighter",
            locked_slot_ids=[str(locked_slot.id)],
        )

        assert str(locked_slot.id) in ai.last_refinement_request.locked_slot_ids

    async def test_passes_user_message_to_ai(self):
        template = make_template(1)
        ai = FakeAIPort(recipes_to_return=[make_recipe()])
        use_case = RefineRecipesUseCase(
            ai_adapter=ai,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(),
            preference_repo=InMemoryPreferenceRepository(),
        )

        await use_case.execute(
            existing_assignments={},
            user_message="make it vegetarian",
        )

        assert ai.last_refinement_request.user_message == "make it vegetarian"

    async def test_raises_when_no_template(self):
        use_case = build_use_case(template=None)

        with pytest.raises(ValueError, match="template"):
            await use_case.execute(existing_assignments={}, user_message="test")

    async def test_passes_existing_assignments_to_ai(self):
        template = make_template(2)
        ai = FakeAIPort(recipes_to_return=[make_recipe(), make_recipe()])
        use_case = RefineRecipesUseCase(
            ai_adapter=ai,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(),
            preference_repo=InMemoryPreferenceRepository(),
        )
        existing = {str(template.slots[0].id): make_recipe("Pasta")}

        await use_case.execute(
            existing_assignments=existing,
            user_message="swap the pasta",
        )

        assert str(template.slots[0].id) in ai.last_refinement_request.existing_assignments
