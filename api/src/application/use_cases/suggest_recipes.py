from dataclasses import dataclass
from typing import Dict, List, Optional

from domain.entities.meal_plan import MealSlot
from domain.entities.recipe import Recipe
from domain.repositories.household_repository import HouseholdRepository
from domain.repositories.meal_plan_repository import MealPlanTemplateRepository
from domain.repositories.preference_repository import PreferenceRepository
from application.ports.ai_port import AIPort, SuggestionRequest


@dataclass
class RecipeSuggestion:
    """Used by ConfirmPlanUseCase — carries the single chosen recipe per slot."""
    slot: MealSlot
    recipe: Recipe


@dataclass
class SlotOptions:
    slot: MealSlot
    options: List[Recipe]  # always 3 candidates


class SuggestRecipesUseCase:
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

    async def execute(self, week_context: Optional[str] = None) -> List[SlotOptions]:
        template = await self._template_repo.get_template()
        if not template or not template.slots:
            raise ValueError("No meal plan template configured.")

        members = await self._household_repo.get_members()
        preferences = await self._preference_repo.get_preferences()

        request = SuggestionRequest(
            slots=template.slots,
            members=members,
            disliked_ingredients=preferences.disliked_ingredients if preferences else [],
            liked_ingredients=preferences.liked_ingredients if preferences else [],
            cuisine_preferences=preferences.cuisine_preferences if preferences else [],
            week_context=week_context,
        )

        options_lists = await self._ai.suggest_recipes(request)

        return [
            SlotOptions(slot=slot, options=options)
            for slot, options in zip(template.slots, options_lists)
        ]

    async def execute_for_slot(
        self,
        slot_id: str,
        existing_chosen: Dict[str, Recipe],
        week_context: Optional[str] = None,
    ) -> SlotOptions:
        """Suggest 3 fresh options for a single slot, using existing assignments as context."""
        template = await self._template_repo.get_template()
        if not template or not template.slots:
            raise ValueError("No meal plan template configured.")

        slot = next((s for s in template.slots if str(s.id) == slot_id), None)
        if not slot:
            raise ValueError(f"Slot '{slot_id}' not found in template.")

        members = await self._household_repo.get_members()
        preferences = await self._preference_repo.get_preferences()

        # Incorporate existing chosen recipes as context to avoid duplication
        context_parts: List[str] = []
        if week_context:
            context_parts.append(week_context)
        if existing_chosen:
            names = ", ".join(r.name for r in existing_chosen.values())
            context_parts.append(
                f"Other slots already have: {names} — suggest something different"
            )

        request = SuggestionRequest(
            slots=[slot],
            members=members,
            disliked_ingredients=preferences.disliked_ingredients if preferences else [],
            liked_ingredients=preferences.liked_ingredients if preferences else [],
            cuisine_preferences=preferences.cuisine_preferences if preferences else [],
            week_context="; ".join(context_parts) if context_parts else None,
        )

        options_lists = await self._ai.suggest_recipes(request)
        return SlotOptions(slot=slot, options=options_lists[0])
