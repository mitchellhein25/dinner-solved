from typing import Dict, List, Optional

from domain.entities.recipe import Recipe
from domain.repositories.household_repository import HouseholdRepository
from domain.repositories.meal_plan_repository import MealPlanTemplateRepository
from domain.repositories.preference_repository import PreferenceRepository
from application.ports.ai_port import AIPort, RefinementRequest
from application.use_cases.suggest_recipes import SlotOptions


class RefineRecipesUseCase:
    def __init__(
        self,
        ai_adapter: AIPort,
        template_repo: MealPlanTemplateRepository,
        household_repo: HouseholdRepository,
        preference_repo: PreferenceRepository,
    ):
        self._ai = ai_adapter
        self._template_repo = template_repo
        self._household_repo = household_repo
        self._preference_repo = preference_repo

    async def execute(
        self,
        existing_assignments: Dict[str, Recipe],  # slot_id (str) -> Recipe
        user_message: str,
        locked_slot_ids: Optional[List[str]] = None,
    ) -> List[SlotOptions]:
        """
        Refine recipes for unlocked slots only.
        Returns SlotOptions only for the unlocked slots.
        """
        if locked_slot_ids is None:
            locked_slot_ids = []

        template = await self._template_repo.get_template()
        if not template or not template.slots:
            raise ValueError("No meal plan template configured.")

        members = await self._household_repo.get_members()
        preferences = await self._preference_repo.get_preferences()

        request = RefinementRequest(
            slots=template.slots,
            members=members,
            disliked_ingredients=preferences.disliked_ingredients if preferences else [],
            liked_ingredients=preferences.liked_ingredients if preferences else [],
            cuisine_preferences=preferences.cuisine_preferences if preferences else [],
            existing_assignments=existing_assignments,
            user_message=user_message,
            locked_slot_ids=locked_slot_ids,
        )

        # The AI adapter handles filtering; it returns options for unlocked slots only
        options_lists = await self._ai.refine_recipes(request)

        unlocked_slots = [
            s for s in template.slots if str(s.id) not in locked_slot_ids
        ]

        return [
            SlotOptions(slot=slot, options=options)
            for slot, options in zip(unlocked_slots, options_lists)
        ]
