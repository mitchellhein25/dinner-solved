from abc import ABC, abstractmethod
from typing import List

from domain.entities.grocery import GroceryListItem


class ExportPort(ABC):
    @abstractmethod
    async def export(self, items: List[GroceryListItem], week_start_date: str) -> str:
        # Returns a URL, file path, or confirmation string depending on adapter
        ...
