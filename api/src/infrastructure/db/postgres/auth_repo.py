from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import HouseholdRow, MagicLinkTokenRow

TOKEN_TTL_MINUTES = 15


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_or_create_household(self, email: str) -> HouseholdRow:
        result = await self._session.execute(
            select(HouseholdRow).where(HouseholdRow.email == email)
        )
        row = result.scalar_one_or_none()
        if row:
            return row
        row = HouseholdRow(id=uuid4(), email=email)
        self._session.add(row)
        await self._session.flush()
        return row

    async def create_magic_token(self, household_id: UUID) -> str:
        token = uuid4()
        row = MagicLinkTokenRow(
            id=uuid4(),
            household_id=household_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MINUTES),
        )
        self._session.add(row)
        await self._session.flush()
        return str(token)

    async def validate_and_consume_token(self, token_str: str) -> Optional[UUID]:
        try:
            token_uuid = UUID(token_str)
        except ValueError:
            return None

        result = await self._session.execute(
            select(MagicLinkTokenRow).where(MagicLinkTokenRow.token == token_uuid)
        )
        row = result.scalar_one_or_none()

        if not row:
            return None
        if row.used_at is not None:
            return None
        if datetime.utcnow() > row.expires_at:
            return None

        row.used_at = datetime.utcnow()
        await self._session.flush()
        return row.household_id

    async def household_exists(self, household_id: UUID) -> bool:
        result = await self._session.execute(
            select(HouseholdRow.id).where(HouseholdRow.id == household_id)
        )
        return result.scalar_one_or_none() is not None
