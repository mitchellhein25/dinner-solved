from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import HouseholdRow, MagicLinkTokenRow, MealPlanTemplateRow

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

    async def validate_and_consume_token(self, token_str: str) -> Optional[tuple[UUID, str]]:
        try:
            token_uuid = UUID(token_str)
        except ValueError:
            return None

        result = await self._session.execute(
            select(MagicLinkTokenRow, HouseholdRow)
            .join(HouseholdRow, HouseholdRow.id == MagicLinkTokenRow.household_id)
            .where(MagicLinkTokenRow.token == token_uuid)
        )
        pair = result.one_or_none()

        if not pair:
            return None
        token_row, household_row = pair
        if token_row.used_at is not None:
            return None
        if datetime.utcnow() > token_row.expires_at:
            return None

        token_row.used_at = datetime.utcnow()
        await self._session.flush()
        return token_row.household_id, household_row.email

    async def household_exists(self, household_id: UUID) -> bool:
        result = await self._session.execute(
            select(HouseholdRow.id).where(HouseholdRow.id == household_id)
        )
        return result.scalar_one_or_none() is not None

    async def has_meal_template(self, household_id: UUID) -> bool:
        result = await self._session.execute(
            select(MealPlanTemplateRow.id).where(MealPlanTemplateRow.household_id == household_id)
        )
        return result.scalar_one_or_none() is not None
