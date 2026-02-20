from abc import ABC, abstractmethod
from typing import Optional

from ..entities.preferences import UserPreferences


class PreferenceRepository(ABC):
    @abstractmethod
    async def get_preferences(self) -> Optional[UserPreferences]: ...

    @abstractmethod
    async def save_preferences(self, preferences: UserPreferences) -> None: ...
