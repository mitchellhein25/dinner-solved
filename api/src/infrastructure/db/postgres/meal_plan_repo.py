from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.entities.meal_plan import (
    DayOfWeek,
    MealPlanTemplate,
    MealSlot,
    MealType,
    SlotAssignment,
    WeeklyPlan,
)
from domain.repositories.meal_plan_repository import (
    MealPlanTemplateRepository,
    WeeklyPlanRepository,
)
from .models import (
    MealPlanTemplateRow,
    MealSlotMemberRow,
    MealSlotRow,
    SlotAssignmentRow,
    WeeklyPlanRow,
)


class PostgresMealPlanTemplateRepository(MealPlanTemplateRepository):
    def __init__(self, session: AsyncSession, household_id: UUID):
        self._session = session
        self._household_id = household_id

    async def get_template(self) -> Optional[MealPlanTemplate]:
        result = await self._session.execute(
            select(MealPlanTemplateRow)
            .where(MealPlanTemplateRow.household_id == self._household_id)
            .options(
                selectinload(MealPlanTemplateRow.slots).selectinload(MealSlotRow.slot_members)
            )
            .order_by(MealPlanTemplateRow.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return self._template_to_entity(row) if row else None

    async def save_template(self, template: MealPlanTemplate) -> None:
        # Delete all existing templates for this household (one template at a time)
        existing = await self._session.execute(
            select(MealPlanTemplateRow).where(MealPlanTemplateRow.household_id == self._household_id)
        )
        for row in existing.scalars().all():
            await self._session.delete(row)
        await self._session.flush()

        template_row = MealPlanTemplateRow(id=template.id, household_id=self._household_id)
        for slot in template.slots:
            slot_row = MealSlotRow(
                id=slot.id,
                name=slot.name,
                meal_type=slot.meal_type.value,
                days=[d.value for d in slot.days],
            )
            for member_id in slot.member_ids:
                slot_row.slot_members.append(MealSlotMemberRow(member_id=member_id))
            template_row.slots.append(slot_row)

        self._session.add(template_row)
        await self._session.flush()

    @staticmethod
    def _template_to_entity(row: MealPlanTemplateRow) -> MealPlanTemplate:
        slots = [
            MealSlot(
                id=slot_row.id,
                name=slot_row.name,
                meal_type=MealType(slot_row.meal_type),
                days=[DayOfWeek(d) for d in slot_row.days],
                member_ids=[sm.member_id for sm in slot_row.slot_members],
            )
            for slot_row in row.slots
        ]
        return MealPlanTemplate(id=row.id, slots=slots)


class PostgresWeeklyPlanRepository(WeeklyPlanRepository):
    def __init__(self, session: AsyncSession, household_id: UUID):
        self._session = session
        self._household_id = household_id

    async def get_plan(self, week_start_date: str) -> Optional[WeeklyPlan]:
        result = await self._session.execute(
            select(WeeklyPlanRow)
            .where(
                WeeklyPlanRow.household_id == self._household_id,
                WeeklyPlanRow.week_start_date == week_start_date,
            )
            .options(selectinload(WeeklyPlanRow.assignments))
        )
        row = result.scalar_one_or_none()
        return self._plan_to_entity(row) if row else None

    async def save_plan(self, plan: WeeklyPlan) -> None:
        # Delete existing plan for this household + week if present
        existing = await self._session.execute(
            select(WeeklyPlanRow).where(
                WeeklyPlanRow.household_id == self._household_id,
                WeeklyPlanRow.week_start_date == plan.week_start_date,
            )
        )
        existing_row = existing.scalar_one_or_none()
        if existing_row:
            await self._session.delete(existing_row)
            await self._session.flush()

        plan_row = WeeklyPlanRow(
            id=plan.id,
            household_id=self._household_id,
            week_start_date=plan.week_start_date,
        )
        for assignment in plan.assignments:
            plan_row.assignments.append(SlotAssignmentRow(
                id=uuid4(),
                slot_id=assignment.slot_id,
                recipe_id=assignment.recipe_id,
            ))
        self._session.add(plan_row)
        await self._session.flush()

    @staticmethod
    def _plan_to_entity(row: WeeklyPlanRow) -> WeeklyPlan:
        return WeeklyPlan(
            id=row.id,
            week_start_date=row.week_start_date,
            assignments=[
                SlotAssignment(slot_id=a.slot_id, recipe_id=a.recipe_id)
                for a in row.assignments
            ],
        )
