from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.preferences import UserPreferences
from domain.repositories.preference_repository import PreferenceRepository
from .models import UserPreferencesRow


class PostgresPreferenceRepository(PreferenceRepository):
    def __init__(self, session: AsyncSession, household_id: UUID):
        self._session = session
        self._household_id = household_id

    async def get_preferences(self) -> Optional[UserPreferences]:
        result = await self._session.execute(
            select(UserPreferencesRow).where(UserPreferencesRow.household_id == self._household_id)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def save_preferences(self, preferences: UserPreferences) -> None:
        existing = await self._session.execute(
            select(UserPreferencesRow).where(UserPreferencesRow.household_id == self._household_id)
        )
        row = existing.scalar_one_or_none()

        if row:
            row.liked_ingredients = preferences.liked_ingredients
            row.disliked_ingredients = preferences.disliked_ingredients
            row.cuisine_preferences = preferences.cuisine_preferences
        else:
            self._session.add(UserPreferencesRow(
                id=preferences.id,
                household_id=self._household_id,
                liked_ingredients=preferences.liked_ingredients,
                disliked_ingredients=preferences.disliked_ingredients,
                cuisine_preferences=preferences.cuisine_preferences,
            ))
        await self._session.flush()

    @staticmethod
    def _to_entity(row: UserPreferencesRow) -> UserPreferences:
        return UserPreferences(
            id=row.id,
            liked_ingredients=list(row.liked_ingredients or []),
            disliked_ingredients=list(row.disliked_ingredients or []),
            cuisine_preferences=list(row.cuisine_preferences or []),
        )
