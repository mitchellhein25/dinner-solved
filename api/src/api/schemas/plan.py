from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .recipe import RecipeListItemSchema, RecipeSchema


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


# ---------------------------------------------------------------------------
# Confirm — unchanged: frontend sends 1 chosen recipe per slot
# ---------------------------------------------------------------------------

class RecipeSuggestionSchema(BaseModel):
    slot: MealSlotSchema
    recipe: RecipeSchema


class ConfirmRequest(BaseModel):
    week_start_date: str
    suggestions: list[RecipeSuggestionSchema]


class WeeklyPlanSchema(BaseModel):
    id: UUID
    week_start_date: str
    assignments: list[dict]  # {slot_id, recipe_id}


class ConfirmedAssignmentSchema(BaseModel):
    slot_id: UUID
    recipe: RecipeListItemSchema


class ConfirmedPlanSchema(BaseModel):
    week_start_date: str
    assignments: list[ConfirmedAssignmentSchema]


# ---------------------------------------------------------------------------
# New 3-option flow
# ---------------------------------------------------------------------------

class RecipeOptionsSchema(BaseModel):
    slot: MealSlotSchema
    options: list[RecipeSchema]  # exactly 3 items


class SlotOptionsResponse(BaseModel):
    slot_options: list[RecipeOptionsSchema]
    budget_remaining: float
    budget_resets_at: datetime | None = None


class SuggestRequest(BaseModel):
    week_context: str | None = None


class RegenerateSlotRequest(BaseModel):
    slot_id: str
    existing_chosen: dict[str, RecipeSchema]  # slot_id -> currently chosen recipe
    week_context: str | None = None


class RefineRequest(BaseModel):
    existing_assignments: dict[str, RecipeSchema]  # slot_id -> recipe
    user_message: str
    locked_slot_ids: list[str] = []
