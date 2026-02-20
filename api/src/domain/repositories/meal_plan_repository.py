from abc import ABC, abstractmethod
from typing import Optional

from ..entities.meal_plan import MealPlanTemplate, WeeklyPlan


class MealPlanTemplateRepository(ABC):
    @abstractmethod
    async def get_template(self) -> Optional[MealPlanTemplate]: ...

    @abstractmethod
    async def save_template(self, template: MealPlanTemplate) -> None: ...


class WeeklyPlanRepository(ABC):
    @abstractmethod
    async def get_plan(self, week_start_date: str) -> Optional[WeeklyPlan]: ...

    @abstractmethod
    async def save_plan(self, plan: WeeklyPlan) -> None: ...
