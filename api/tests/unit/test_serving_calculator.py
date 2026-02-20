import uuid

import pytest

from domain.entities.household import HouseholdMember
from domain.entities.meal_plan import DayOfWeek, MealSlot, MealType
from domain.services.serving_calculator import ServingCalculator


def make_member(serving_size: float) -> HouseholdMember:
    return HouseholdMember(
        id=uuid.uuid4(),
        name="Test",
        emoji="🧑",
        serving_size=serving_size,
    )


def make_slot(member_ids: list, days: list) -> MealSlot:
    return MealSlot(
        id=uuid.uuid4(),
        name="Test Slot",
        meal_type=MealType.DINNER,
        days=days,
        member_ids=member_ids,
    )


@pytest.fixture
def calc() -> ServingCalculator:
    return ServingCalculator()


class TestServingCalculator:
    def test_single_member_single_day(self, calc):
        member = make_member(1.0)
        slot = make_slot([member.id], [DayOfWeek.MON])

        result = calc.total_servings(slot, [member])

        assert result == 1.0

    def test_single_member_multiple_days(self, calc):
        member = make_member(1.5)
        slot = make_slot(
            [member.id],
            [DayOfWeek.MON, DayOfWeek.WED, DayOfWeek.FRI],
        )

        result = calc.total_servings(slot, [member])

        assert result == 4.5  # 1.5 * 3

    def test_multiple_members_multiple_days(self, calc):
        """The canonical example from the brief: Mitch(1.5) + Wife(1.0) + Daughter(0.25) * 3 days."""
        mitch = make_member(1.5)
        wife = make_member(1.0)
        daughter = make_member(0.25)
        slot = make_slot(
            [mitch.id, wife.id, daughter.id],
            [DayOfWeek.MON, DayOfWeek.TUE, DayOfWeek.WED],
        )

        result = calc.total_servings(slot, [mitch, wife, daughter])

        assert result == 8.25  # (1.5 + 1.0 + 0.25) * 3

    def test_member_not_in_slot_is_excluded(self, calc):
        adult = make_member(1.0)
        baby = make_member(0.25)
        # Slot only includes adult — baby doesn't eat this meal
        slot = make_slot([adult.id], [DayOfWeek.MON, DayOfWeek.TUE])

        result = calc.total_servings(slot, [adult, baby])

        assert result == 2.0  # 1.0 * 2, baby excluded

    def test_fractional_serving_sizes_round_correctly(self, calc):
        """0.25-increment serving sizes should not accumulate floating point error."""
        members = [make_member(0.25) for _ in range(3)]
        slot = make_slot([m.id for m in members], [DayOfWeek.MON, DayOfWeek.TUE])

        result = calc.total_servings(slot, members)

        assert result == 1.5  # (0.25 * 3) * 2

    def test_empty_slot_no_members_returns_zero(self, calc):
        slot = make_slot([], [DayOfWeek.MON])
        member = make_member(1.0)

        result = calc.total_servings(slot, [member])

        assert result == 0.0

    def test_zero_day_slot_returns_zero(self, calc):
        member = make_member(1.0)
        slot = make_slot([member.id], [])

        result = calc.total_servings(slot, [member])

        assert result == 0.0

    def test_result_is_rounded_to_two_decimal_places(self, calc):
        member = make_member(1.0 / 3)  # repeating decimal
        slot = make_slot([member.id], [DayOfWeek.MON])

        result = calc.total_servings(slot, [member])

        # Should be rounded to 2 decimal places, not a long float
        assert result == round(1.0 / 3, 2)
        assert len(str(result).split(".")[-1]) <= 2
