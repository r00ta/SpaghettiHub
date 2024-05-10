from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.models.base import ListResult

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    def __init__(self, connection_provider: ConnectionProvider):
        self.connection_provider = connection_provider

    @abstractmethod
    async def get_next_id(self) -> int:
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        pass

    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    async def list(self, size: int, page: int) -> ListResult[T]:
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        pass

    @abstractmethod
    async def delete(self, id: int) -> None:
        """
        If no resource with such `id` is found, silently ignore it and return `None` in any case.
        """
