from typing import List, Optional
from uuid import UUID

from domain.entities.household import HouseholdMember
from domain.repositories.household_repository import HouseholdRepository


class ManageHouseholdUseCase:
    def __init__(self, household_repo: HouseholdRepository):
        self._repo = household_repo

    async def get_members(self) -> List[HouseholdMember]:
        return await self._repo.get_members()

    async def save_members(self, members: List[HouseholdMember]) -> None:
        await self._repo.save_members(members)

    async def get_member(self, member_id: UUID) -> Optional[HouseholdMember]:
        return await self._repo.get_member(member_id)
