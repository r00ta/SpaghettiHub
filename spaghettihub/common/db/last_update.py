from typing import Optional

from sqlalchemy import delete, insert, select

from spaghettihub.common.db.repository import BaseRepository
from spaghettihub.common.db.tables import LastUpdateTable
from spaghettihub.common.models.base import ListResult
from spaghettihub.common.models.last_update import LastUpdate


class LastUpdateRepository(BaseRepository[LastUpdate]):
    async def get_next_id(self) -> int:
        raise Exception("not implemented")

    async def create(self, entity: LastUpdate) -> LastUpdate:
        stmt = (
            insert(LastUpdateTable)
            .returning(LastUpdateTable.c.id, LastUpdateTable.c.last_updated)
            .values(id=entity.id, last_updated=entity.last_updated)
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        last_update = result.one()
        return LastUpdate(**last_update._asdict())

    async def find_by_id(self, id: int) -> Optional[LastUpdate]:
        stmt = (
            select("*").select_from(LastUpdateTable).where(LastUpdateTable.c.id == id)
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        last_update = result.first()
        if not last_update:
            return None
        return LastUpdate(**last_update._asdict())

    async def list(self, size: int, page: int) -> ListResult[LastUpdate]:
        pass

    async def update(self, entity: LastUpdate) -> LastUpdate:
        pass

    async def delete(self, id: int) -> None:
        await self.connection_provider.get_current_connection().execute(
            delete(LastUpdateTable).where(LastUpdateTable.c.id == id)
        )
