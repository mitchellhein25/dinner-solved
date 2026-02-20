import uuid

import pytest

from application.use_cases.manage_template import ManageTemplateUseCase
from domain.entities.meal_plan import DayOfWeek, MealPlanTemplate, MealSlot, MealType
from domain.services.meal_plan_service import MealPlanService
from tests.unit.fakes import InMemoryMealPlanTemplateRepository


def make_slot(member_ids=None, days=None) -> MealSlot:
    return MealSlot(
        id=uuid.uuid4(),
        name="Dinner",
        meal_type=MealType.DINNER,
        days=[DayOfWeek.MON] if days is None else days,
        member_ids=[uuid.uuid4()] if member_ids is None else member_ids,
    )


@pytest.fixture
def repo():
    return InMemoryMealPlanTemplateRepository()


@pytest.fixture
def use_case(repo):
    return ManageTemplateUseCase(template_repo=repo, meal_plan_service=MealPlanService())


class TestManageTemplate:
    async def test_get_template_returns_none_when_unset(self, use_case):
        result = await use_case.get_template()
        assert result is None

    async def test_save_and_retrieve_template(self, use_case):
        template = MealPlanTemplate(id=uuid.uuid4(), slots=[make_slot()])
        await use_case.save_template(template)

        result = await use_case.get_template()

        assert result is not None
        assert result.id == template.id

    async def test_save_replaces_previous_template(self, use_case):
        template_a = MealPlanTemplate(id=uuid.uuid4(), slots=[make_slot()])
        template_b = MealPlanTemplate(id=uuid.uuid4(), slots=[make_slot(), make_slot()])
        await use_case.save_template(template_a)
        await use_case.save_template(template_b)

        result = await use_case.get_template()

        assert result.id == template_b.id
        assert len(result.slots) == 2

    async def test_save_invalid_template_no_members_raises(self, use_case):
        bad_slot = make_slot(member_ids=[])  # no members
        template = MealPlanTemplate(id=uuid.uuid4(), slots=[bad_slot])

        with pytest.raises(ValueError):
            await use_case.save_template(template)

    async def test_save_invalid_template_no_days_raises(self, use_case):
        bad_slot = make_slot(days=[])  # no days
        template = MealPlanTemplate(id=uuid.uuid4(), slots=[bad_slot])

        with pytest.raises(ValueError):
            await use_case.save_template(template)

    async def test_invalid_template_not_persisted(self, use_case):
        bad_slot = make_slot(member_ids=[])
        template = MealPlanTemplate(id=uuid.uuid4(), slots=[bad_slot])

        with pytest.raises(ValueError):
            await use_case.save_template(template)

        assert await use_case.get_template() is None
