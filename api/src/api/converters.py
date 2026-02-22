"""
Pure functions that convert between domain entities and API schemas.
No business logic — just field mapping.
"""
from domain.entities.grocery import GroceryListItem
from domain.entities.household import HouseholdMember
from domain.entities.meal_plan import DayOfWeek, MealPlanTemplate, MealSlot, MealType
from domain.entities.preferences import UserPreferences
from domain.entities.recipe import GroceryCategory, Ingredient, Recipe
from application.use_cases.suggest_recipes import SlotOptions

from .schemas.grocery import GroceryListItemSchema
from .schemas.household import HouseholdMemberSchema
from .schemas.plan import (
    MealPlanTemplateSchema,
    MealSlotSchema,
    RecipeOptionsSchema,
)
from .schemas.preferences import PreferencesSchema
from .schemas.recipe import IngredientSchema, RecipeDetailSchema, RecipeListItemSchema, RecipeSchema


# ---------------------------------------------------------------------------
# Household
# ---------------------------------------------------------------------------

def member_to_schema(m: HouseholdMember) -> HouseholdMemberSchema:
    return HouseholdMemberSchema(id=m.id, name=m.name, emoji=m.emoji, serving_size=m.serving_size)


def schema_to_member(s: HouseholdMemberSchema) -> HouseholdMember:
    return HouseholdMember(id=s.id, name=s.name, emoji=s.emoji, serving_size=s.serving_size)


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------

def ingredient_to_schema(i: Ingredient) -> IngredientSchema:
    return IngredientSchema(name=i.name, quantity=i.quantity, unit=i.unit, category=i.category.value)


def recipe_to_schema(r: Recipe) -> RecipeSchema:
    return RecipeSchema(
        id=r.id,
        name=r.name,
        emoji=r.emoji,
        prep_time=r.prep_time,
        ingredients=[ingredient_to_schema(i) for i in r.ingredients],
        key_ingredients=r.key_ingredients,
        is_favorite=r.is_favorite,
        source_url=r.source_url,
    )


def recipe_to_list_item(r: Recipe) -> RecipeListItemSchema:
    return RecipeListItemSchema(
        id=r.id,
        name=r.name,
        emoji=r.emoji,
        prep_time=r.prep_time,
        key_ingredients=r.key_ingredients,
        is_favorite=r.is_favorite,
        times_used=r.times_used,
        last_used_at=r.last_used_at,
    )


def recipe_to_detail(r: Recipe) -> RecipeDetailSchema:
    return RecipeDetailSchema(
        id=r.id,
        name=r.name,
        emoji=r.emoji,
        prep_time=r.prep_time,
        ingredients=[ingredient_to_schema(i) for i in r.ingredients],
        key_ingredients=r.key_ingredients,
        is_favorite=r.is_favorite,
        times_used=r.times_used,
        last_used_at=r.last_used_at,
        cooking_instructions=r.cooking_instructions,
        source_url=r.source_url,
    )


def schema_to_recipe(s: RecipeSchema) -> Recipe:
    return Recipe(
        id=s.id,
        name=s.name,
        emoji=s.emoji,
        prep_time=s.prep_time,
        ingredients=[
            Ingredient(
                name=i.name,
                quantity=i.quantity,
                unit=i.unit,
                category=GroceryCategory(i.category),
            )
            for i in s.ingredients
        ],
        key_ingredients=s.key_ingredients,
        is_favorite=s.is_favorite,
        source_url=s.source_url,
    )


# ---------------------------------------------------------------------------
# Meal plan
# ---------------------------------------------------------------------------

def slot_to_schema(s: MealSlot) -> MealSlotSchema:
    return MealSlotSchema(
        id=s.id,
        name=s.name,
        meal_type=s.meal_type.value,
        days=[d.value for d in s.days],
        member_ids=s.member_ids,
    )


def schema_to_slot(s: MealSlotSchema) -> MealSlot:
    return MealSlot(
        id=s.id,
        name=s.name,
        meal_type=MealType(s.meal_type),
        days=[DayOfWeek(d) for d in s.days],
        member_ids=s.member_ids,
    )


def template_to_schema(t: MealPlanTemplate) -> MealPlanTemplateSchema:
    return MealPlanTemplateSchema(id=t.id, slots=[slot_to_schema(s) for s in t.slots])


def schema_to_template(s: MealPlanTemplateSchema) -> MealPlanTemplate:
    return MealPlanTemplate(id=s.id, slots=[schema_to_slot(sl) for sl in s.slots])


def slot_options_to_schema(so: SlotOptions) -> RecipeOptionsSchema:
    return RecipeOptionsSchema(
        slot=slot_to_schema(so.slot),
        options=[recipe_to_schema(r) for r in so.options],
    )


# ---------------------------------------------------------------------------
# Grocery
# ---------------------------------------------------------------------------

def grocery_item_to_schema(item: GroceryListItem) -> GroceryListItemSchema:
    return GroceryListItemSchema(
        name=item.name,
        quantity=item.quantity,
        unit=item.unit,
        category=item.category.value,
        recipe_names=item.recipe_names,
    )


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

def prefs_to_schema(p: UserPreferences) -> PreferencesSchema:
    return PreferencesSchema(
        id=p.id,
        liked_ingredients=p.liked_ingredients,
        disliked_ingredients=p.disliked_ingredients,
        cuisine_preferences=p.cuisine_preferences,
    )


def schema_to_prefs(s: PreferencesSchema) -> UserPreferences:
    return UserPreferences(
        id=s.id,
        liked_ingredients=s.liked_ingredients,
        disliked_ingredients=s.disliked_ingredients,
        cuisine_preferences=s.cuisine_preferences,
    )
