from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class IngredientSchema(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str  # GroceryCategory value


class RecipeInputSchema(BaseModel):
    """Full recipe payload for create (POST) and full update (PUT)."""
    name: str
    emoji: str
    prep_time: int
    ingredients: list[IngredientSchema]
    key_ingredients: list[str]
    source_url: str | None = None
    cooking_instructions: list[str] | None = None


class ImportRecipeRequest(BaseModel):
    url: str


class RecipeSchema(BaseModel):
    """Lightweight schema used in the planning flow (suggest / refine / confirm)."""
    id: UUID
    name: str
    emoji: str
    prep_time: int
    ingredients: list[IngredientSchema]
    key_ingredients: list[str]
    is_favorite: bool = False
    source_url: str | None = None


class RecipeListItemSchema(BaseModel):
    """Summary schema for the recipe repository list view (no ingredients or instructions)."""
    id: UUID
    name: str
    emoji: str
    prep_time: int
    key_ingredients: list[str]
    is_favorite: bool
    times_used: int
    last_used_at: datetime | None = None


class RecipeDetailSchema(BaseModel):
    """Full schema returned by GET /recipes/{id} and PATCH /recipes/{id}/favorite."""
    id: UUID
    name: str
    emoji: str
    prep_time: int
    ingredients: list[IngredientSchema]
    key_ingredients: list[str]
    is_favorite: bool
    times_used: int
    last_used_at: datetime | None = None
    cooking_instructions: list[str] | None = None
    source_url: str | None = None
