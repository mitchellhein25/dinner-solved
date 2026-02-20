from dataclasses import dataclass
from typing import List, Optional

from domain.entities.meal_plan import MealSlot
from domain.entities.recipe import Recipe
from domain.repositories.household_repository import HouseholdRepository
from domain.repositories.meal_plan_repository import MealPlanTemplateRepository
from domain.repositories.preference_repository import PreferenceRepository
from application.ports.ai_port import AIPort, SuggestionRequest


@dataclass
class RecipeSuggestion:
    slot: MealSlot
    recipe: Recipe


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

    async def execute(self, week_context: Optional[str] = None) -> List[RecipeSuggestion]:
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

        recipes = await self._ai.suggest_recipes(request)

        return [
            RecipeSuggestion(slot=slot, recipe=recipe)
            for slot, recipe in zip(template.slots, recipes)
        ]
