from dataclasses import dataclass, field
from typing import List
from uuid import UUID


@dataclass
class UserPreferences:
    id: UUID
    liked_ingredients: List[str] = field(default_factory=list)
    disliked_ingredients: List[str] = field(default_factory=list)
    cuisine_preferences: List[str] = field(default_factory=list)
