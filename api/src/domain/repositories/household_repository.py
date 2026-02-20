from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.household import HouseholdMember


class HouseholdRepository(ABC):
    @abstractmethod
    async def get_members(self) -> List[HouseholdMember]: ...

    @abstractmethod
    async def save_members(self, members: List[HouseholdMember]) -> None: ...

    @abstractmethod
    async def get_member(self, member_id: UUID) -> Optional[HouseholdMember]: ...
