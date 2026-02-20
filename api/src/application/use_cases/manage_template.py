from typing import Optional

from domain.entities.meal_plan import MealPlanTemplate
from domain.repositories.meal_plan_repository import MealPlanTemplateRepository
from domain.services.meal_plan_service import MealPlanService


class ManageTemplateUseCase:
    def __init__(
        self,
        template_repo: MealPlanTemplateRepository,
        meal_plan_service: MealPlanService,
    ):
        self._repo = template_repo
        self._service = meal_plan_service

    async def get_template(self) -> Optional[MealPlanTemplate]:
        return await self._repo.get_template()

    async def save_template(self, template: MealPlanTemplate) -> None:
        if not self._service.validate_template(template):
            raise ValueError(
                "Invalid template: every slot must have at least one member and one day assigned."
            )
        await self._repo.save_template(template)
