from dataclasses import dataclass, field
from enum import Enum
from typing import List
from uuid import UUID


class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class DayOfWeek(Enum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


@dataclass
class MealSlot:
    id: UUID
    name: str  # e.g. "Weekday Lunches", "Dinner A"
    meal_type: MealType
    days: List[DayOfWeek]  # which days this slot covers
    member_ids: List[UUID]  # which household members eat this meal

    @property
    def day_count(self) -> int:
        return len(self.days)


@dataclass
class MealPlanTemplate:
    id: UUID
    slots: List[MealSlot]


@dataclass
class SlotAssignment:
    slot_id: UUID
    recipe_id: UUID


@dataclass
class WeeklyPlan:
    id: UUID
    week_start_date: str  # ISO date string, e.g. "2026-02-23"
    assignments: List[SlotAssignment]
