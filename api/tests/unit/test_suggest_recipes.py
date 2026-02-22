import uuid

import pytest

from application.use_cases.suggest_recipes import SlotOptions, SuggestRecipesUseCase
from domain.entities.household import HouseholdMember
from domain.entities.meal_plan import DayOfWeek, MealPlanTemplate, MealSlot, MealType
from domain.entities.preferences import UserPreferences
from domain.entities.recipe import GroceryCategory, Ingredient, Recipe
from tests.unit.fakes import (
    FakeAIPort,
    InMemoryHouseholdRepository,
    InMemoryMealPlanTemplateRepository,
    InMemoryPreferenceRepository,
    InMemoryRecipeRepository,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_member(serving_size: float = 1.0) -> HouseholdMember:
    return HouseholdMember(id=uuid.uuid4(), name="Test", emoji="🧑", serving_size=serving_size)


def make_slot() -> MealSlot:
    return MealSlot(
        id=uuid.uuid4(),
        name="Dinner",
        meal_type=MealType.DINNER,
        days=[DayOfWeek.MON, DayOfWeek.TUE],
        member_ids=[uuid.uuid4()],
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


def make_template(n_slots: int = 1) -> MealPlanTemplate:
    return MealPlanTemplate(id=uuid.uuid4(), slots=[make_slot() for _ in range(n_slots)])


def make_prefs(**kwargs) -> UserPreferences:
    return UserPreferences(id=uuid.uuid4(), **kwargs)


# ---------------------------------------------------------------------------
# Fixture factory
# ---------------------------------------------------------------------------

def build_use_case(
    template=None,
    members=None,
    preferences=None,
    recipes_to_return=None,
    recipe_repo=None,
) -> SuggestRecipesUseCase:
    return SuggestRecipesUseCase(
        ai_adapter=FakeAIPort(recipes_to_return=recipes_to_return or []),
        template_repo=InMemoryMealPlanTemplateRepository(template=template),
        household_repo=InMemoryHouseholdRepository(members=members or []),
        preference_repo=InMemoryPreferenceRepository(preferences=preferences),
        recipe_repo=recipe_repo or InMemoryRecipeRepository(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSuggestRecipes:
    async def test_returns_one_slot_options_per_slot(self):
        template = make_template(n_slots=3)
        recipes = [make_recipe(f"Recipe {i}") for i in range(3)]
        use_case = build_use_case(template=template, recipes_to_return=recipes)

        result = await use_case.execute()

        assert len(result) == 3
        assert all(isinstance(s, SlotOptions) for s in result)

    async def test_each_slot_options_has_three_choices(self):
        template = make_template(n_slots=2)
        recipes = [make_recipe("Chicken"), make_recipe("Salmon")]
        use_case = build_use_case(template=template, recipes_to_return=recipes)

        result = await use_case.execute()

        assert len(result[0].options) == 3
        assert len(result[1].options) == 3

    async def test_each_slot_options_pairs_correct_slot(self):
        template = make_template(n_slots=2)
        recipes = [make_recipe("Chicken"), make_recipe("Salmon")]
        use_case = build_use_case(template=template, recipes_to_return=recipes)

        result = await use_case.execute()

        assert result[0].slot.id == template.slots[0].id
        assert result[0].options[0].name == "Chicken"
        assert result[1].slot.id == template.slots[1].id
        assert result[1].options[0].name == "Salmon"

    async def test_raises_when_no_template(self):
        use_case = build_use_case(template=None)

        with pytest.raises(ValueError, match="template"):
            await use_case.execute()

    async def test_raises_when_template_has_no_slots(self):
        template = MealPlanTemplate(id=uuid.uuid4(), slots=[])
        use_case = build_use_case(template=template)

        with pytest.raises(ValueError):
            await use_case.execute()

    async def test_passes_preferences_to_ai(self):
        template = make_template(1)
        prefs = make_prefs(
            liked_ingredients=["garlic"],
            disliked_ingredients=["cilantro"],
            cuisine_preferences=["Italian"],
        )
        ai = FakeAIPort(recipes_to_return=[make_recipe()])
        use_case = SuggestRecipesUseCase(
            ai_adapter=ai,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(),
            preference_repo=InMemoryPreferenceRepository(preferences=prefs),
            recipe_repo=InMemoryRecipeRepository(),
        )

        await use_case.execute()

        req = ai.last_suggestion_request
        assert req.liked_ingredients == ["garlic"]
        assert req.disliked_ingredients == ["cilantro"]
        assert req.cuisine_preferences == ["Italian"]

    async def test_works_with_no_preferences(self):
        template = make_template(1)
        use_case = build_use_case(
            template=template,
            preferences=None,
            recipes_to_return=[make_recipe()],
        )

        result = await use_case.execute()

        assert len(result) == 1

    async def test_passes_week_context_to_ai(self):
        template = make_template(1)
        ai = FakeAIPort(recipes_to_return=[make_recipe()])
        use_case = SuggestRecipesUseCase(
            ai_adapter=ai,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(),
            preference_repo=InMemoryPreferenceRepository(),
            recipe_repo=InMemoryRecipeRepository(),
        )

        await use_case.execute(week_context="feeling like something light")

        assert ai.last_suggestion_request.week_context == "feeling like something light"

    async def test_passes_members_to_ai(self):
        template = make_template(1)
        members = [make_member(1.0), make_member(0.5)]
        ai = FakeAIPort(recipes_to_return=[make_recipe()])
        use_case = SuggestRecipesUseCase(
            ai_adapter=ai,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(members=members),
            preference_repo=InMemoryPreferenceRepository(),
            recipe_repo=InMemoryRecipeRepository(),
        )

        await use_case.execute()

        assert len(ai.last_suggestion_request.members) == 2

    async def test_execute_for_slot_returns_single_slot_options(self):
        template = make_template(n_slots=2)
        target_slot = template.slots[0]
        recipe = make_recipe("Tacos")
        ai = FakeAIPort(recipes_to_return=[recipe])
        use_case = SuggestRecipesUseCase(
            ai_adapter=ai,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(),
            preference_repo=InMemoryPreferenceRepository(),
            recipe_repo=InMemoryRecipeRepository(),
        )

        result = await use_case.execute_for_slot(
            slot_id=str(target_slot.id), existing_chosen={}
        )

        assert isinstance(result, SlotOptions)
        assert result.slot.id == target_slot.id
        assert len(result.options) == 3

    async def test_execute_for_slot_raises_on_unknown_slot(self):
        template = make_template(1)
        use_case = build_use_case(template=template, recipes_to_return=[make_recipe()])

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute_for_slot(
                slot_id=str(uuid.uuid4()), existing_chosen={}
            )

    async def test_execute_for_slot_includes_existing_context(self):
        template = make_template(2)
        recipe = make_recipe("Tacos")
        ai = FakeAIPort(recipes_to_return=[recipe])
        use_case = SuggestRecipesUseCase(
            ai_adapter=ai,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(),
            preference_repo=InMemoryPreferenceRepository(),
            recipe_repo=InMemoryRecipeRepository(),
        )
        existing = {str(template.slots[1].id): make_recipe("Pasta")}

        await use_case.execute_for_slot(
            slot_id=str(template.slots[0].id), existing_chosen=existing
        )

        # Week context should include existing recipe names
        req = ai.last_suggestion_request
        assert req.week_context is not None
        assert "Pasta" in req.week_context

    async def test_recent_recipe_names_passed_to_ai(self):
        from datetime import datetime, timezone

        template = make_template(1)
        ai = FakeAIPort(recipes_to_return=[make_recipe()])

        # Pre-seed the recipe repo with a recently used recipe
        recent_recipe = Recipe(
            id=uuid.uuid4(),
            name="Old Favourite",
            emoji="🍲",
            prep_time=20,
            ingredients=[],
            key_ingredients=[],
            times_used=3,
            last_used_at=datetime.now(timezone.utc),
        )
        repo = InMemoryRecipeRepository()
        repo._recipes[recent_recipe.id] = recent_recipe

        use_case = SuggestRecipesUseCase(
            ai_adapter=ai,
            template_repo=InMemoryMealPlanTemplateRepository(template=template),
            household_repo=InMemoryHouseholdRepository(),
            preference_repo=InMemoryPreferenceRepository(),
            recipe_repo=repo,
        )

        await use_case.execute()

        assert "Old Favourite" in ai.last_suggestion_request.recent_recipe_names
