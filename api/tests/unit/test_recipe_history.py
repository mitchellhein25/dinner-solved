"""
Tests for recipe persistence, upsert logic, and the new use cases.
"""
from dataclasses import replace
from uuid import uuid4

import pytest

from application.use_cases.confirm_plan import ConfirmPlanUseCase
from application.use_cases.generate_instructions import GenerateInstructionsUseCase
from application.use_cases.get_recipe import GetRecipeUseCase
from application.use_cases.list_recipes import ListRecipesUseCase
from application.use_cases.suggest_recipes import RecipeSuggestion
from application.use_cases.toggle_favorite import ToggleFavoriteUseCase
from domain.entities.meal_plan import DayOfWeek, MealSlot, MealType
from domain.entities.recipe import GroceryCategory, Ingredient, Recipe
from tests.unit.fakes import (
    FakeAIPort,
    InMemoryRecipeRepository,
    InMemoryWeeklyPlanRepository,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_recipe(name: str = "Pasta Carbonara") -> Recipe:
    return Recipe(
        id=uuid4(),
        name=name,
        emoji="🍝",
        prep_time=30,
        ingredients=[
            Ingredient(name="pasta", quantity=100, unit="g", category=GroceryCategory.PANTRY)
        ],
        key_ingredients=["pasta", "eggs"],
    )


def make_slot() -> MealSlot:
    return MealSlot(
        id=uuid4(),
        name="Dinner A",
        meal_type=MealType.DINNER,
        days=[DayOfWeek.MON, DayOfWeek.TUE],
        member_ids=[],
    )


# ---------------------------------------------------------------------------
# InMemoryRecipeRepository — upsert logic
# ---------------------------------------------------------------------------

async def test_save_recipe_new_inserts_and_returns_recipe():
    repo = InMemoryRecipeRepository()
    recipe = make_recipe()
    saved = await repo.save_recipe(recipe)
    assert saved.id == recipe.id
    assert saved.times_used == 1
    assert saved.last_used_at is not None


async def test_save_recipe_uuid_match_updates_and_returns_canonical_id():
    repo = InMemoryRecipeRepository()
    recipe = make_recipe()
    await repo.save_recipe(recipe)

    updated = replace(recipe, emoji="🍜")
    saved = await repo.save_recipe(updated)

    assert saved.id == recipe.id          # canonical id preserved
    assert saved.times_used == 2
    assert saved.emoji == "🍜"
    assert len(await repo.get_recipes()) == 1  # no duplicate


async def test_save_recipe_name_match_uses_existing_id():
    repo = InMemoryRecipeRepository()
    original = make_recipe("Thai Curry")
    await repo.save_recipe(original)

    # New recipe with different UUID but same name
    new_uuid = uuid4()
    duplicate = replace(make_recipe("Thai Curry"), id=new_uuid)
    saved = await repo.save_recipe(duplicate)

    assert saved.id == original.id   # canonical id from first insert
    assert saved.id != new_uuid
    assert saved.times_used == 2
    assert len(await repo.get_recipes()) == 1


async def test_save_recipe_different_names_creates_two_rows():
    repo = InMemoryRecipeRepository()
    await repo.save_recipe(make_recipe("Pasta"))
    await repo.save_recipe(make_recipe("Salad"))
    assert len(await repo.get_recipes()) == 2


# ---------------------------------------------------------------------------
# InMemoryRecipeRepository — sort / filter
# ---------------------------------------------------------------------------

async def test_get_recipes_favorites_only():
    repo = InMemoryRecipeRepository()
    r1 = await repo.save_recipe(make_recipe("A"))
    r2 = make_recipe("B")
    r2 = replace(r2, is_favorite=True)
    await repo.save_recipe(r2)

    faves = await repo.get_recipes(favorites_only=True)
    assert len(faves) == 1
    assert faves[0].name == "B"


async def test_get_recipes_sort_alpha():
    repo = InMemoryRecipeRepository()
    for name in ["Zucchini Soup", "Apple Tart", "Mushroom Risotto"]:
        await repo.save_recipe(make_recipe(name))
    result = await repo.get_recipes(sort="alpha")
    assert [r.name for r in result] == ["Apple Tart", "Mushroom Risotto", "Zucchini Soup"]


async def test_get_recipes_sort_most_used():
    repo = InMemoryRecipeRepository()
    r = make_recipe("Popular")
    await repo.save_recipe(r)
    await repo.save_recipe(r)   # times_used = 2
    await repo.save_recipe(make_recipe("Once"))  # times_used = 1
    result = await repo.get_recipes(sort="most_used")
    assert result[0].name == "Popular"


# ---------------------------------------------------------------------------
# InMemoryRecipeRepository — save_instructions / toggle_favorite
# ---------------------------------------------------------------------------

async def test_save_instructions_persists_to_recipe():
    repo = InMemoryRecipeRepository()
    recipe = await repo.save_recipe(make_recipe())
    await repo.save_instructions(recipe.id, ["Step 1.", "Step 2."])
    fetched = await repo.get_recipe(recipe.id)
    assert fetched.cooking_instructions == ["Step 1.", "Step 2."]


async def test_toggle_favorite_returns_updated_recipe():
    repo = InMemoryRecipeRepository()
    recipe = await repo.save_recipe(make_recipe())
    assert recipe.is_favorite is False

    toggled = await repo.toggle_favorite(recipe.id)
    assert toggled.is_favorite is True

    toggled_back = await repo.toggle_favorite(recipe.id)
    assert toggled_back.is_favorite is False


async def test_toggle_favorite_unknown_id_returns_none():
    repo = InMemoryRecipeRepository()
    result = await repo.toggle_favorite(uuid4())
    assert result is None


# ---------------------------------------------------------------------------
# ConfirmPlanUseCase — canonical id used in assignments
# ---------------------------------------------------------------------------

async def test_confirm_uses_canonical_id_when_name_matched():
    recipe_repo = InMemoryRecipeRepository()
    plan_repo = InMemoryWeeklyPlanRepository()

    # Pre-existing recipe with a known UUID
    original = make_recipe("Chicken Stir Fry")
    await recipe_repo.save_recipe(original)

    # AI generates the same recipe with a NEW UUID
    ai_recipe = replace(make_recipe("Chicken Stir Fry"), id=uuid4())
    slot = make_slot()
    suggestion = RecipeSuggestion(slot=slot, recipe=ai_recipe)

    use_case = ConfirmPlanUseCase(plan_repo=plan_repo, recipe_repo=recipe_repo)
    plan = await use_case.execute(week_start_date="2026-02-24", suggestions=[suggestion])

    # The plan assignment must reference the original (canonical) UUID
    assert plan.assignments[0].recipe_id == original.id
    assert len(await recipe_repo.get_recipes()) == 1


# ---------------------------------------------------------------------------
# GenerateInstructionsUseCase — lazy instruction generation
# ---------------------------------------------------------------------------

async def test_generate_instructions_generates_on_first_fetch():
    repo = InMemoryRecipeRepository()
    ai = FakeAIPort()
    recipe = await repo.save_recipe(make_recipe())
    assert recipe.cooking_instructions is None

    use_case = GenerateInstructionsUseCase(recipe_repo=repo, ai_port=ai)
    result = await use_case.execute(recipe.id)

    assert result.cooking_instructions is not None
    assert len(result.cooking_instructions) > 0
    # Should be cached now
    cached = await repo.get_recipe(recipe.id)
    assert cached.cooking_instructions == result.cooking_instructions


async def test_generate_instructions_skips_when_instructions_exist():
    repo = InMemoryRecipeRepository()
    ai = FakeAIPort()
    recipe = await repo.save_recipe(make_recipe())
    await repo.save_instructions(recipe.id, ["Already done."])

    use_case = GenerateInstructionsUseCase(recipe_repo=repo, ai_port=ai)
    result = await use_case.execute(recipe.id)

    assert result.cooking_instructions == ["Already done."]
    assert ai.last_instructions_recipe is None  # AI never called


async def test_generate_instructions_returns_none_for_unknown_id():
    repo = InMemoryRecipeRepository()
    ai = FakeAIPort()
    use_case = GenerateInstructionsUseCase(recipe_repo=repo, ai_port=ai)
    assert await use_case.execute(uuid4()) is None


# ---------------------------------------------------------------------------
# GetRecipeUseCase — immediate return without generation
# ---------------------------------------------------------------------------

async def test_get_recipe_returns_none_for_unknown_id():
    repo = InMemoryRecipeRepository()
    use_case = GetRecipeUseCase(recipe_repo=repo)
    assert await use_case.execute(uuid4()) is None


async def test_get_recipe_returns_recipe_without_generating_instructions():
    repo = InMemoryRecipeRepository()
    recipe = await repo.save_recipe(make_recipe())
    use_case = GetRecipeUseCase(recipe_repo=repo)
    result = await use_case.execute(recipe.id)
    # cooking_instructions is None because we didn't call GenerateInstructionsUseCase
    assert result is not None
    assert result.cooking_instructions is None


# ---------------------------------------------------------------------------
# ListRecipesUseCase
# ---------------------------------------------------------------------------

async def test_list_recipes_delegates_sort_and_filter():
    repo = InMemoryRecipeRepository()
    for name in ["Zzz", "Aaa"]:
        await repo.save_recipe(make_recipe(name))

    use_case = ListRecipesUseCase(recipe_repo=repo)
    result = await use_case.execute(sort="alpha")
    assert result[0].name == "Aaa"


# ---------------------------------------------------------------------------
# ToggleFavoriteUseCase
# ---------------------------------------------------------------------------

async def test_toggle_favorite_use_case():
    repo = InMemoryRecipeRepository()
    recipe = await repo.save_recipe(make_recipe())

    use_case = ToggleFavoriteUseCase(recipe_repo=repo)
    result = await use_case.execute(recipe.id)
    assert result.is_favorite is True
