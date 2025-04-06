from typing import Optional

from sqlalchemy import delete, insert, select, update, desc
from sqlalchemy.sql.functions import count

from spaghettihub.common.db.repository import BaseRepository
from spaghettihub.common.db.sequences import (MAASSequence)
from spaghettihub.common.db.tables import (MAASTable)
from spaghettihub.common.models.base import ListResult
from spaghettihub.common.models.maas import MAAS


class MAASRepository(BaseRepository[MAAS]):
    async def get_next_id(self) -> int:
        stmt = select(MAASSequence.next_value())
        return (
            await self.connection_provider.get_current_connection().execute(stmt)
        ).scalar()

    async def create(self, entity: MAAS) -> MAAS:
        stmt = (
            insert(MAASTable)
            .returning(
                MAASTable
            )
            .values(**entity.dict())
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        row = result.one()
        return MAAS(**row._asdict())

    async def find_by_id(self, id: int) -> Optional[MAAS]:
        stmt = select("*").select_from(MAASTable).where(MAASTable.c.id == id)
        result = await self.connection_provider.get_current_connection().execute(stmt)
        maas = result.first()
        if not maas:
            return None
        return MAAS(**maas._asdict())

    async def find_by_sha(self, sha: str) -> Optional[MAAS]:
        stmt = select("*").select_from(MAASTable).where(MAASTable.c.commit_sha == sha)
        result = await self.connection_provider.get_current_connection().execute(stmt)
        maas = result.first()
        if not maas:
            return None
        return MAAS(**maas._asdict())

    async def list_commits(self, query: str | None, size: int, page: int) -> ListResult[MAAS]:
        total_stmt = select(count()).select_from(MAASTable).where(
            MAASTable.c.commit_sha.like("%" + query + "%"))
        total = (await self.connection_provider.get_current_connection().execute(total_stmt)).scalar()

        stmt = (
            select("*")
            .select_from(MAASTable)
            .where(MAASTable.c.commit_sha.like("%" + query + "%"))
            .order_by(desc(MAASTable.c.commit_date))
            .offset((page - 1) * size)
            .limit(size)
        )

        result = await self.connection_provider.get_current_connection().execute(stmt)
        return ListResult[MAAS](
            items=[MAAS(**row._asdict()) for row in result.all()],
            total=total
        )
    async def update(self, entity: MAAS) -> MAAS:
        stmt = (
            update(MAASTable)
            .where(MAASTable.c.id == entity.id)
            .values(**entity.dict())
        )
        await self.connection_provider.get_current_connection().execute(stmt)
        return entity

    async def delete(self, id: str) -> None:
        await self.connection_provider.get_current_connection().execute(delete(MAASTable).where(MAASTable.c.id == id))
