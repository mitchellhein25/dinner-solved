"""
Tests for user-added recipe use cases:
  - ImportRecipeUseCase (AI URL parsing)
  - CreateRecipeUseCase (manual / post-import save)
  - FullUpdateRecipeUseCase (full field edit)

Also covers the new InMemoryRecipeRepository methods: create_recipe, full_update_recipe.
"""
from dataclasses import replace
from uuid import uuid4

import pytest

from application.use_cases.create_recipe import CreateRecipeUseCase
from application.use_cases.full_update_recipe import FullUpdateRecipeUseCase
from application.use_cases.import_recipe import ImportRecipeUseCase
from domain.entities.recipe import GroceryCategory, Ingredient, Recipe
from tests.unit.fakes import FakeAIPort, InMemoryRecipeRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_recipe(name: str = "Roast Chicken") -> Recipe:
    return Recipe(
        id=uuid4(),
        name=name,
        emoji="🍗",
        prep_time=45,
        ingredients=[
            Ingredient(name="chicken", quantity=1.5, unit="lbs", category=GroceryCategory.MEAT)
        ],
        key_ingredients=["chicken", "lemon"],
    )


def make_ingredient(name: str = "garlic") -> Ingredient:
    return Ingredient(name=name, quantity=2, unit="cloves", category=GroceryCategory.PRODUCE)


# ---------------------------------------------------------------------------
# ImportRecipeUseCase
# ---------------------------------------------------------------------------

async def test_import_recipe_returns_recipe_from_ai():
    ai = FakeAIPort()
    use_case = ImportRecipeUseCase(ai_port=ai)
    result = await use_case.execute("https://example.com/recipe")
    assert result is not None
    assert result.name == "Parsed Recipe"


async def test_import_recipe_raises_when_ai_raises():
    class FailingAIPort(FakeAIPort):
        async def parse_recipe_from_url(self, url: str) -> Recipe:
            raise ValueError("No recipe found")

    use_case = ImportRecipeUseCase(ai_port=FailingAIPort())
    with pytest.raises(ValueError, match="No recipe found"):
        await use_case.execute("https://example.com/not-a-recipe")


async def test_import_recipe_does_not_persist():
    """Imported draft must not touch any repository."""
    ai = FakeAIPort()
    use_case = ImportRecipeUseCase(ai_port=ai)
    await use_case.execute("https://example.com/recipe")
    # No repo involved — just verifying the use case doesn't try to save anything.
    # If it did, it would require a repo arg and the test would fail to construct.


# ---------------------------------------------------------------------------
# CreateRecipeUseCase
# ---------------------------------------------------------------------------

async def test_create_recipe_saves_with_zero_usage():
    repo = InMemoryRecipeRepository()
    use_case = CreateRecipeUseCase(recipe_repo=repo)
    recipe = make_recipe("Lemon Pasta")
    saved = await use_case.execute(recipe)
    assert saved.name == "Lemon Pasta"
    assert saved.times_used == 0
    assert saved.last_used_at is None


async def test_create_recipe_appears_in_list():
    repo = InMemoryRecipeRepository()
    use_case = CreateRecipeUseCase(recipe_repo=repo)
    recipe = make_recipe("Caesar Salad")
    await use_case.execute(recipe)
    all_recipes = await repo.get_recipes()
    assert any(r.name == "Caesar Salad" for r in all_recipes)


async def test_create_recipe_preserves_instructions():
    repo = InMemoryRecipeRepository()
    use_case = CreateRecipeUseCase(recipe_repo=repo)
    recipe = replace(make_recipe(), cooking_instructions=["Step 1.", "Step 2."])
    saved = await use_case.execute(recipe)
    assert saved.cooking_instructions == ["Step 1.", "Step 2."]


async def test_create_recipe_preserves_source_url():
    repo = InMemoryRecipeRepository()
    use_case = CreateRecipeUseCase(recipe_repo=repo)
    recipe = replace(make_recipe(), source_url="https://example.com/recipe")
    saved = await use_case.execute(recipe)
    assert saved.source_url == "https://example.com/recipe"


async def test_create_recipe_raises_on_name_collision():
    repo = InMemoryRecipeRepository()
    use_case = CreateRecipeUseCase(recipe_repo=repo)
    recipe = make_recipe("Bolognese")
    await use_case.execute(recipe)
    with pytest.raises(ValueError, match="already exists"):
        await use_case.execute(replace(make_recipe("Bolognese"), id=uuid4()))


async def test_create_recipe_does_not_collide_with_save_recipe():
    """save_recipe (upsert) and create_recipe are separate paths; both can coexist."""
    repo = InMemoryRecipeRepository()
    use_case = CreateRecipeUseCase(recipe_repo=repo)

    # save_recipe inserts one record (confirm flow)
    confirmed = make_recipe("Stir Fry")
    await repo.save_recipe(confirmed)
    assert len(await repo.get_recipes()) == 1

    # create_recipe for a differently-named recipe should succeed
    await use_case.execute(make_recipe("Fried Rice"))
    assert len(await repo.get_recipes()) == 2


# ---------------------------------------------------------------------------
# InMemoryRecipeRepository — create_recipe
# ---------------------------------------------------------------------------

async def test_repo_create_recipe_times_used_zero():
    repo = InMemoryRecipeRepository()
    saved = await repo.create_recipe(make_recipe())
    assert saved.times_used == 0
    assert saved.last_used_at is None


async def test_repo_create_recipe_name_collision_raises():
    repo = InMemoryRecipeRepository()
    await repo.create_recipe(make_recipe("Tagine"))
    with pytest.raises(ValueError):
        await repo.create_recipe(replace(make_recipe("Tagine"), id=uuid4()))


async def test_repo_create_recipe_does_not_collide_with_different_names():
    repo = InMemoryRecipeRepository()
    a = await repo.create_recipe(make_recipe("Soup"))
    b = await repo.create_recipe(make_recipe("Salad"))
    assert a.name == "Soup"
    assert b.name == "Salad"
    assert len(await repo.get_recipes()) == 2


# ---------------------------------------------------------------------------
# FullUpdateRecipeUseCase
# ---------------------------------------------------------------------------

async def test_full_update_changes_all_fields():
    repo = InMemoryRecipeRepository()
    original = await repo.create_recipe(make_recipe("Old Name"))
    new_ingredients = [make_ingredient("onion"), make_ingredient("tomato")]

    use_case = FullUpdateRecipeUseCase(recipe_repo=repo)
    updated = await use_case.execute(
        recipe_id=original.id,
        name="New Name",
        emoji="🥘",
        prep_time=60,
        key_ingredients=["onion", "tomato"],
        ingredients=new_ingredients,
        source_url="https://example.com/new",
        cooking_instructions=["Chop.", "Cook.", "Serve."],
    )

    assert updated.name == "New Name"
    assert updated.emoji == "🥘"
    assert updated.prep_time == 60
    assert updated.key_ingredients == ["onion", "tomato"]
    assert len(updated.ingredients) == 2
    assert updated.source_url == "https://example.com/new"
    assert updated.cooking_instructions == ["Chop.", "Cook.", "Serve."]


async def test_full_update_returns_none_for_unknown_id():
    repo = InMemoryRecipeRepository()
    use_case = FullUpdateRecipeUseCase(recipe_repo=repo)
    result = await use_case.execute(
        recipe_id=uuid4(),
        name="Ghost",
        emoji="👻",
        prep_time=10,
        key_ingredients=[],
        ingredients=[],
        source_url=None,
        cooking_instructions=None,
    )
    assert result is None


async def test_full_update_raises_on_name_collision_with_other_recipe():
    repo = InMemoryRecipeRepository()
    r1 = await repo.create_recipe(make_recipe("Recipe A"))
    await repo.create_recipe(make_recipe("Recipe B"))

    use_case = FullUpdateRecipeUseCase(recipe_repo=repo)
    with pytest.raises(ValueError, match="already exists"):
        await use_case.execute(
            recipe_id=r1.id,
            name="Recipe B",  # collision with r2
            emoji="🍽️",
            prep_time=30,
            key_ingredients=[],
            ingredients=[],
            source_url=None,
            cooking_instructions=None,
        )


async def test_full_update_allows_keeping_same_name():
    """Renaming a recipe to its own current name should not raise."""
    repo = InMemoryRecipeRepository()
    recipe = await repo.create_recipe(make_recipe("My Recipe"))

    use_case = FullUpdateRecipeUseCase(recipe_repo=repo)
    updated = await use_case.execute(
        recipe_id=recipe.id,
        name="My Recipe",  # same name — no collision
        emoji="✨",
        prep_time=20,
        key_ingredients=["a"],
        ingredients=[],
        source_url=None,
        cooking_instructions=None,
    )
    assert updated.emoji == "✨"


async def test_full_update_preserves_times_used():
    """Full edit should not reset usage statistics."""
    repo = InMemoryRecipeRepository()
    # Simulate a recipe that has been confirmed multiple times
    base = make_recipe("Popular Dish")
    await repo.save_recipe(base)
    await repo.save_recipe(base)  # times_used = 2
    recipe = (await repo.get_recipes())[0]
    assert recipe.times_used == 2

    use_case = FullUpdateRecipeUseCase(recipe_repo=repo)
    updated = await use_case.execute(
        recipe_id=recipe.id,
        name="Popular Dish",
        emoji="⭐",
        prep_time=25,
        key_ingredients=["x"],
        ingredients=[],
        source_url=None,
        cooking_instructions=None,
    )
    assert updated.times_used == 2


# ---------------------------------------------------------------------------
# InMemoryRecipeRepository — full_update_recipe
# ---------------------------------------------------------------------------

async def test_repo_full_update_replaces_ingredients():
    repo = InMemoryRecipeRepository()
    recipe = await repo.create_recipe(make_recipe())
    assert len(recipe.ingredients) == 1

    new_ings = [make_ingredient("garlic"), make_ingredient("onion"), make_ingredient("tomato")]
    updated = await repo.full_update_recipe(
        recipe_id=recipe.id,
        name=recipe.name,
        emoji=recipe.emoji,
        prep_time=recipe.prep_time,
        key_ingredients=recipe.key_ingredients,
        ingredients=new_ings,
        source_url=None,
        cooking_instructions=None,
    )
    assert len(updated.ingredients) == 3


async def test_repo_full_update_clears_instructions_when_none():
    repo = InMemoryRecipeRepository()
    recipe = replace(make_recipe(), cooking_instructions=["Step 1."])
    saved = await repo.create_recipe(recipe)

    updated = await repo.full_update_recipe(
        recipe_id=saved.id,
        name=saved.name,
        emoji=saved.emoji,
        prep_time=saved.prep_time,
        key_ingredients=saved.key_ingredients,
        ingredients=saved.ingredients,
        source_url=None,
        cooking_instructions=None,
    )
    assert updated.cooking_instructions is None
