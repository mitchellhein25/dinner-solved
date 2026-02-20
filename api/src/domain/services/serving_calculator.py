from typing import List

from ..entities.household import HouseholdMember
from ..entities.meal_plan import MealSlot


class ServingCalculator:
    def total_servings(self, slot: MealSlot, members: List[HouseholdMember]) -> float:
        """
        Sum serving sizes of members assigned to this slot,
        multiplied by the number of days the slot covers.

        Example: Mitch(1.5) + Wife(1.0) + Daughter(0.25) = 2.75 × 3 days = 8.25
        """
        slot_members = [m for m in members if m.id in slot.member_ids]
        per_meal = sum(m.serving_size for m in slot_members)
        return round(per_meal * slot.day_count, 2)
