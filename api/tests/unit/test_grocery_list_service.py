import uuid
from typing import Dict

import pytest

from domain.entities.grocery import GroceryListItem
from domain.entities.household import HouseholdMember
from domain.entities.meal_plan import (
    DayOfWeek,
    MealSlot,
    MealType,
    SlotAssignment,
    WeeklyPlan,
)
from domain.entities.recipe import GroceryCategory, Ingredient, Recipe
from domain.services.grocery_list_service import GroceryListService
from domain.services.serving_calculator import ServingCalculator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def member(serving_size: float) -> HouseholdMember:
    return HouseholdMember(
        id=uuid.uuid4(), name="Test", emoji="🧑", serving_size=serving_size
    )


def slot(member_ids: list, days: list) -> MealSlot:
    return MealSlot(
        id=uuid.uuid4(),
        name="Slot",
        meal_type=MealType.DINNER,
        days=days,
        member_ids=member_ids,
    )


def ingredient(name: str, qty: float, unit: str, category: GroceryCategory) -> Ingredient:
    return Ingredient(name=name, quantity=qty, unit=unit, category=category)


def recipe(*ingredients: Ingredient, name: str = "Recipe") -> Recipe:
    return Recipe(
        id=uuid.uuid4(),
        name=name,
        emoji="🍽️",
        prep_time=30,
        ingredients=list(ingredients),
        key_ingredients=[],
    )


def plan(assignments: list) -> WeeklyPlan:
    return WeeklyPlan(
        id=uuid.uuid4(),
        week_start_date="2026-02-23",
        assignments=assignments,
    )


def assignment(s: MealSlot, r: Recipe) -> SlotAssignment:
    return SlotAssignment(slot_id=s.id, recipe_id=r.id)


def recipes_map(*rs: Recipe) -> Dict[str, Recipe]:
    return {str(r.id): r for r in rs}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def service() -> GroceryListService:
    return GroceryListService(serving_calculator=ServingCalculator())


class TestGroceryListServiceBuild:
    def test_single_recipe_single_slot_single_day(self, service):
        m = member(1.0)
        s = slot([m.id], [DayOfWeek.MON])
        r = recipe(
            ingredient("Chicken breast", 0.5, "lbs", GroceryCategory.MEAT),
            name="Grilled Chicken",
        )
        wp = plan([assignment(s, r)])

        result = service.build(wp, [s], [m], recipes_map(r))

        assert len(result) == 1
        assert result[0].name == "Chicken breast"
        assert result[0].quantity == 0.5  # 0.5 * 1 serving * 1 day

    def test_ingredient_scaled_by_servings_and_days(self, service):
        """Mitch(1.5) + Wife(1.0) = 2.5 per meal * 3 days = 7.5 total servings."""
        m1 = member(1.5)
        m2 = member(1.0)
        s = slot([m1.id, m2.id], [DayOfWeek.MON, DayOfWeek.WED, DayOfWeek.FRI])
        r = recipe(
            ingredient("Pasta", 2.0, "oz", GroceryCategory.PANTRY),
            name="Pasta Night",
        )
        wp = plan([assignment(s, r)])

        result = service.build(wp, [s], [m1, m2], recipes_map(r))

        assert result[0].quantity == 15.0  # 2.0 * 7.5

    def test_duplicate_ingredients_merged_across_recipes(self, service):
        """Same ingredient in two recipes → quantities summed, recipe_names combined."""
        m = member(1.0)
        s1 = slot([m.id], [DayOfWeek.MON])
        s2 = slot([m.id], [DayOfWeek.TUE])
        r1 = recipe(
            ingredient("Olive oil", 1.0, "tbsp", GroceryCategory.PANTRY),
            name="Recipe A",
        )
        r2 = recipe(
            ingredient("Olive oil", 2.0, "tbsp", GroceryCategory.PANTRY),
            name="Recipe B",
        )
        wp = plan([assignment(s1, r1), assignment(s2, r2)])

        result = service.build(wp, [s1, s2], [m], recipes_map(r1, r2))

        assert len(result) == 1
        assert result[0].name == "Olive oil"
        assert result[0].quantity == 3.0
        assert "Recipe A" in result[0].recipe_names
        assert "Recipe B" in result[0].recipe_names

    def test_different_units_not_merged(self, service):
        """Chicken in 'lbs' and 'oz' should remain separate line items."""
        m = member(1.0)
        s1 = slot([m.id], [DayOfWeek.MON])
        s2 = slot([m.id], [DayOfWeek.TUE])
        r1 = recipe(
            ingredient("Chicken", 1.0, "lbs", GroceryCategory.MEAT), name="Recipe A"
        )
        r2 = recipe(
            ingredient("Chicken", 8.0, "oz", GroceryCategory.MEAT), name="Recipe B"
        )
        wp = plan([assignment(s1, r1), assignment(s2, r2)])

        result = service.build(wp, [s1, s2], [m], recipes_map(r1, r2))

        assert len(result) == 2
        units = {item.unit for item in result}
        assert units == {"lbs", "oz"}

    def test_items_sorted_by_category_then_name(self, service):
        m = member(1.0)
        s = slot([m.id], [DayOfWeek.MON])
        r = recipe(
            ingredient("Zucchini", 1.0, "whole", GroceryCategory.PRODUCE),
            ingredient("Milk", 1.0, "cups", GroceryCategory.DAIRY),
            ingredient("Beef", 1.0, "lbs", GroceryCategory.MEAT),
            ingredient("Apple", 1.0, "whole", GroceryCategory.PRODUCE),
            name="Mixed Recipe",
        )
        wp = plan([assignment(s, r)])

        result = service.build(wp, [s], [m], recipes_map(r))

        categories = [item.category for item in result]
        names = [item.name for item in result]

        # PRODUCE comes before MEAT, DAIRY (enum order: produce=0, meat=1, dairy=2)
        produce_indices = [i for i, c in enumerate(categories) if c == GroceryCategory.PRODUCE]
        meat_indices = [i for i, c in enumerate(categories) if c == GroceryCategory.MEAT]
        dairy_indices = [i for i, c in enumerate(categories) if c == GroceryCategory.DAIRY]

        assert max(produce_indices) < min(meat_indices)
        assert max(meat_indices) < min(dairy_indices)

        # Within PRODUCE, alphabetical: Apple before Zucchini
        produce_names = [names[i] for i in produce_indices]
        assert produce_names == sorted(produce_names, key=str.lower)

    def test_recipe_names_attributed_to_each_item(self, service):
        m = member(1.0)
        s = slot([m.id], [DayOfWeek.MON])
        r = recipe(
            ingredient("Garlic", 2.0, "cloves", GroceryCategory.PRODUCE),
            name="Garlic Pasta",
        )
        wp = plan([assignment(s, r)])

        result = service.build(wp, [s], [m], recipes_map(r))

        assert result[0].recipe_names == ["Garlic Pasta"]

    def test_same_recipe_attribution_not_duplicated_on_merge(self, service):
        """If two slots use the same recipe, the recipe name should appear once."""
        m = member(1.0)
        s1 = slot([m.id], [DayOfWeek.MON])
        s2 = slot([m.id], [DayOfWeek.TUE])
        r = recipe(
            ingredient("Rice", 1.0, "cups", GroceryCategory.PANTRY),
            name="Rice Bowl",
        )
        wp = plan([assignment(s1, r), assignment(s2, r)])

        result = service.build(wp, [s1, s2], [m], recipes_map(r))

        assert len(result) == 1
        assert result[0].recipe_names.count("Rice Bowl") == 1

    def test_multiple_slots_with_different_members(self, service):
        """Two slots with different member compositions are scaled independently."""
        adult = member(1.0)
        child = member(0.5)

        # Slot 1: adult only, 2 days → 2.0 total servings
        s1 = slot([adult.id], [DayOfWeek.MON, DayOfWeek.TUE])
        # Slot 2: adult + child, 1 day → 1.5 total servings
        s2 = slot([adult.id, child.id], [DayOfWeek.WED])

        r1 = recipe(
            ingredient("Salmon", 1.0, "lbs", GroceryCategory.MEAT), name="Salmon Dish"
        )
        r2 = recipe(
            ingredient("Tofu", 1.0, "lbs", GroceryCategory.MEAT), name="Tofu Dish"
        )
        wp = plan([assignment(s1, r1), assignment(s2, r2)])

        result = service.build(wp, [s1, s2], [adult, child], recipes_map(r1, r2))

        salmon = next(i for i in result if i.name == "Salmon")
        tofu = next(i for i in result if i.name == "Tofu")

        assert salmon.quantity == 2.0   # 1.0 * 2.0
        assert tofu.quantity == 1.5     # 1.0 * 1.5

    def test_empty_plan_returns_empty_list(self, service):
        wp = plan([])

        result = service.build(wp, [], [], {})

        assert result == []

    def test_quantity_rounded_to_two_decimal_places(self, service):
        m = member(1.0 / 3)  # produces repeating decimal
        s = slot([m.id], [DayOfWeek.MON])
        r = recipe(
            ingredient("Butter", 3.0, "tbsp", GroceryCategory.DAIRY),
            name="Butter Recipe",
        )
        wp = plan([assignment(s, r)])

        result = service.build(wp, [s], [m], recipes_map(r))

        qty_str = str(result[0].quantity)
        decimal_part = qty_str.split(".")[-1] if "." in qty_str else ""
        assert len(decimal_part) <= 2
