from dataclasses import dataclass
from uuid import UUID


@dataclass
class HouseholdMember:
    id: UUID
    name: str
    emoji: str
    serving_size: float  # multiplier against 1 standard serving, e.g. 1.5, 1.0, 0.25
