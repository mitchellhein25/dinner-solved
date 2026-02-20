from uuid import UUID

from pydantic import BaseModel


class IngredientSchema(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str  # GroceryCategory value


class RecipeSchema(BaseModel):
    id: UUID
    name: str
    emoji: str
    prep_time: int
    ingredients: list[IngredientSchema]
    key_ingredients: list[str]
    is_favorite: bool = False
    source_url: str | None = None
