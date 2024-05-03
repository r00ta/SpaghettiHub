from typing import List, Optional

from sqlalchemy import delete, insert, select
from sqlalchemy.sql.operators import eq

from launchpadllm.common.db.repository import BaseRepository
from launchpadllm.common.db.sequences import MyTextSequence
from launchpadllm.common.db.tables import EmbeddingTable, MyTextTable
from launchpadllm.common.models.base import ListResult
from launchpadllm.common.models.texts import MyText


class TextsRepository(BaseRepository[MyText]):
    async def get_next_id(self) -> int:
        stmt = select(MyTextSequence.next_value())
        return (
            await self.connection_provider.get_current_connection().execute(stmt)
        ).scalar()

    async def create(self, entity: MyText) -> MyText:
        stmt = (
            insert(MyTextTable)
            .returning(MyTextTable.c.id, MyTextTable.c.content)
            .values(id=entity.id, content=entity.content)
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        text = result.one()
        return MyText(**text._asdict())

    async def find_by_id(self, id: int) -> Optional[MyText]:
        stmt = select(
            "*").select_from(MyTextTable).where(MyTextTable.c.id == id)
        result = await self.connection_provider.get_current_connection().execute(stmt)
        text = result.first()
        if not text:
            return None
        return MyText(**text._asdict())

    async def list(self, size: int, page: int) -> ListResult[MyText]:
        pass

    async def update(self, entity: MyText) -> MyText:
        pass

    async def delete(self, id: int) -> None:
        await self.connection_provider.get_current_connection().execute(
            delete(MyTextTable).where(MyTextTable.c.id == id)
        )

    async def find_texts_without_embeddings(self) -> List[MyText]:
        stmt = (
            select(MyTextTable.c.id, MyTextTable.c.content)
            .select_from(MyTextTable)
            .join(
                EmbeddingTable,
                eq(EmbeddingTable.c.text_id, MyTextTable.c.id),
                isouter=True,
            )
            .where(eq(EmbeddingTable.c.text_id, None))
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        return [MyText(**row._asdict()) for row in result.all()]
