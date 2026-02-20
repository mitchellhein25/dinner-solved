from uuid import UUID

from pydantic import BaseModel

from .recipe import RecipeSchema


class MealSlotSchema(BaseModel):
    id: UUID
    name: str
    meal_type: str
    days: list[str]
    member_ids: list[UUID]


class MealPlanTemplateSchema(BaseModel):
    id: UUID
    slots: list[MealSlotSchema]


class SaveTemplateRequest(BaseModel):
    template: MealPlanTemplateSchema


class RecipeSuggestionSchema(BaseModel):
    slot: MealSlotSchema
    recipe: RecipeSchema


class SuggestRequest(BaseModel):
    week_context: str | None = None


class RefineRequest(BaseModel):
    existing_assignments: dict[str, RecipeSchema]  # slot_id -> recipe
    user_message: str
    slot_id_to_refine: str | None = None


class ConfirmRequest(BaseModel):
    week_start_date: str
    suggestions: list[RecipeSuggestionSchema]


class WeeklyPlanSchema(BaseModel):
    id: UUID
    week_start_date: str
    assignments: list[dict]  # {slot_id, recipe_id}


class SuggestionsResponse(BaseModel):
    suggestions: list[RecipeSuggestionSchema]
