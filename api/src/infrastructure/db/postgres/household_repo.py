from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.household import HouseholdMember
from domain.repositories.household_repository import HouseholdRepository
from .models import HouseholdMemberRow


class PostgresHouseholdRepository(HouseholdRepository):
    def __init__(self, session: AsyncSession, household_id: UUID):
        self._session = session
        self._household_id = household_id

    async def get_members(self) -> List[HouseholdMember]:
        result = await self._session.execute(
            select(HouseholdMemberRow).where(HouseholdMemberRow.household_id == self._household_id)
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def save_members(self, members: List[HouseholdMember]) -> None:
        # Replace all members for this household atomically
        await self._session.execute(
            delete(HouseholdMemberRow).where(HouseholdMemberRow.household_id == self._household_id)
        )
        for member in members:
            self._session.add(HouseholdMemberRow(
                id=member.id,
                household_id=self._household_id,
                name=member.name,
                emoji=member.emoji,
                serving_size=member.serving_size,
            ))
        await self._session.flush()

    async def get_member(self, member_id: UUID) -> Optional[HouseholdMember]:
        result = await self._session.execute(
            select(HouseholdMemberRow).where(
                HouseholdMemberRow.id == member_id,
                HouseholdMemberRow.household_id == self._household_id,
            )
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    @staticmethod
    def _to_entity(row: HouseholdMemberRow) -> HouseholdMember:
        return HouseholdMember(
            id=row.id,
            name=row.name,
            emoji=row.emoji,
            serving_size=row.serving_size,
        )
