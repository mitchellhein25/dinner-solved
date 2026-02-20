from typing import List

from ..entities.meal_plan import MealPlanTemplate, MealSlot, WeeklyPlan


class MealPlanService:
    """Validates and queries meal plan state."""

    def validate_template(self, template: MealPlanTemplate) -> bool:
        """Return True if every slot has at least one member and one day assigned."""
        return all(
            len(slot.member_ids) > 0 and len(slot.days) > 0
            for slot in template.slots
        )

    def assigned_slots(
        self,
        template: MealPlanTemplate,
        plan: WeeklyPlan,
    ) -> List[MealSlot]:
        """Return the template slots that have a recipe assigned in the given plan."""
        assigned_slot_ids = {a.slot_id for a in plan.assignments}
        return [s for s in template.slots if s.id in assigned_slot_ids]
