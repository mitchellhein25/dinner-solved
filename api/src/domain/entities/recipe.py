from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID


class GroceryCategory(Enum):
    PRODUCE = "produce"
    MEAT = "meat"
    DAIRY = "dairy"
    PANTRY = "pantry"
    FROZEN = "frozen"
    BAKERY = "bakery"
    OTHER = "other"


@dataclass
class Ingredient:
    name: str
    quantity: float
    unit: str  # 'lbs', 'oz', 'cups', 'tbsp', 'tsp', 'whole', etc.
    category: GroceryCategory
    # IMPORTANT: quantity is always for 1 standard serving.
    # GroceryListService handles all scaling.


@dataclass
class Recipe:
    id: UUID
    name: str
    emoji: str
    prep_time: int  # minutes
    ingredients: List[Ingredient]
    key_ingredients: List[str]  # short summary for display, e.g. ['chicken', 'rice']
    is_favorite: bool = False
    source_url: Optional[str] = None
    cooking_instructions: Optional[List[str]] = None  # None until generated on demand
    times_used: int = 0
    last_used_at: Optional[datetime] = None
