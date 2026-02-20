from dataclasses import dataclass, field
from typing import List

from .recipe import GroceryCategory


@dataclass
class GroceryListItem:
    name: str
    quantity: float
    unit: str
    category: GroceryCategory
    recipe_names: List[str]  # which recipes contributed this item
