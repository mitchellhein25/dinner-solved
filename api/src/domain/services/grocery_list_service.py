from typing import Dict, List

from ..entities.grocery import GroceryListItem
from ..entities.household import HouseholdMember
from ..entities.meal_plan import MealSlot, WeeklyPlan
from ..entities.recipe import GroceryCategory, Recipe
from .serving_calculator import ServingCalculator


class GroceryListService:
    def __init__(self, serving_calculator: ServingCalculator):
        self._calc = serving_calculator

    def build(
        self,
        weekly_plan: WeeklyPlan,
        slots: List[MealSlot],
        members: List[HouseholdMember],
        recipes: Dict[str, Recipe],  # recipe_id (str) -> Recipe
    ) -> List[GroceryListItem]:
        """
        For each slot assignment:
          1. Calculate total servings = sum(member.serving_size) * slot.day_count
          2. Scale each ingredient by total servings
          3. Merge duplicate ingredients (same name + unit) across all recipes
          4. Return sorted by category then name
        """
        raw_items: List[GroceryListItem] = []

        for assignment in weekly_plan.assignments:
            slot = next(s for s in slots if s.id == assignment.slot_id)
            recipe = recipes[str(assignment.recipe_id)]
            total_servings = self._calc.total_servings(slot, members)

            for ingredient in recipe.ingredients:
                raw_items.append(
                    GroceryListItem(
                        name=ingredient.name,
                        quantity=round(ingredient.quantity * total_servings, 2),
                        unit=ingredient.unit,
                        category=ingredient.category,
                        recipe_names=[recipe.name],
                    )
                )

        return self._merge_and_sort(raw_items)

    def _merge_and_sort(self, items: List[GroceryListItem]) -> List[GroceryListItem]:
        # Key: (lowercase name, unit) — items with the same name+unit are merged
        merged: Dict[tuple, GroceryListItem] = {}

        for item in items:
            key = (item.name.lower(), item.unit)
            if key in merged:
                existing = merged[key]
                new_recipe_names = existing.recipe_names + [
                    r for r in item.recipe_names if r not in existing.recipe_names
                ]
                merged[key] = GroceryListItem(
                    name=existing.name,
                    quantity=round(existing.quantity + item.quantity, 2),
                    unit=existing.unit,
                    category=existing.category,
                    recipe_names=new_recipe_names,
                )
            else:
                merged[key] = GroceryListItem(
                    name=item.name,
                    quantity=item.quantity,
                    unit=item.unit,
                    category=item.category,
                    recipe_names=list(item.recipe_names),
                )

        category_order = list(GroceryCategory)
        return sorted(
            merged.values(),
            key=lambda i: (category_order.index(i.category), i.name.lower()),
        )
