import uuid

import pytest

from application.use_cases.manage_household import ManageHouseholdUseCase
from domain.entities.household import HouseholdMember
from tests.unit.fakes import InMemoryHouseholdRepository


def make_member(name: str = "Alice", serving_size: float = 1.0) -> HouseholdMember:
    return HouseholdMember(id=uuid.uuid4(), name=name, emoji="🧑", serving_size=serving_size)


@pytest.fixture
def repo():
    return InMemoryHouseholdRepository()


@pytest.fixture
def use_case(repo):
    return ManageHouseholdUseCase(household_repo=repo)


class TestManageHousehold:
    async def test_get_members_empty_by_default(self, use_case):
        result = await use_case.get_members()
        assert result == []

    async def test_save_and_retrieve_members(self, use_case):
        members = [make_member("Alice"), make_member("Bob")]
        await use_case.save_members(members)

        result = await use_case.get_members()

        assert len(result) == 2
        assert {m.name for m in result} == {"Alice", "Bob"}

    async def test_save_replaces_existing_members(self, use_case):
        await use_case.save_members([make_member("Alice")])
        await use_case.save_members([make_member("Bob"), make_member("Carol")])

        result = await use_case.get_members()

        assert len(result) == 2
        assert {m.name for m in result} == {"Bob", "Carol"}

    async def test_get_member_by_id_returns_correct_member(self, use_case):
        alice = make_member("Alice")
        bob = make_member("Bob")
        await use_case.save_members([alice, bob])

        result = await use_case.get_member(alice.id)

        assert result is not None
        assert result.name == "Alice"

    async def test_get_member_unknown_id_returns_none(self, use_case):
        await use_case.save_members([make_member("Alice")])

        result = await use_case.get_member(uuid.uuid4())

        assert result is None
