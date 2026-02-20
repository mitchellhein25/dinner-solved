from typing import Dict, List, Optional

from domain.entities.recipe import Recipe
from domain.repositories.household_repository import HouseholdRepository
from domain.repositories.meal_plan_repository import MealPlanTemplateRepository
from domain.repositories.preference_repository import PreferenceRepository
from application.ports.ai_port import AIPort, RefinementRequest
from application.use_cases.suggest_recipes import RecipeSuggestion


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
        slot_id_to_refine: Optional[str] = None,
    ) -> List[RecipeSuggestion]:
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
            slot_id_to_refine=slot_id_to_refine,
        )

        recipes = await self._ai.refine_recipes(request)

        return [
            RecipeSuggestion(slot=slot, recipe=recipe)
            for slot, recipe in zip(template.slots, recipes)
        ]
