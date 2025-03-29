from typing import Optional

from sqlalchemy import delete, desc, insert, select
from sqlalchemy.sql.functions import count

from spaghettihub.common.db.repository import BaseRepository
from spaghettihub.common.db.sequences import EmbeddingSequence
from spaghettihub.common.db.tables import EmbeddingTable
from spaghettihub.common.models.base import ListResult, OneToOne
from spaghettihub.common.models.embeddings import Embedding
from spaghettihub.common.models.texts import MyText


class EmbeddingsRepository(BaseRepository[Embedding]):
    async def get_next_id(self) -> int:
        stmt = select(EmbeddingSequence.next_value())
        return (
            await self.connection_provider.get_current_connection().execute(stmt)
        ).scalar()

    async def create(self, entity: Embedding) -> Embedding:
        stmt = (
            insert(EmbeddingTable)
            .returning(
                EmbeddingTable.c.id,
                EmbeddingTable.c.text_id,
                EmbeddingTable.c.embedding,
            )
            .values(id=entity.id, text_id=entity.text.id, embedding=entity.embedding)
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        embedding = result.one()
        return Embedding(
            text=OneToOne[MyText](id=embedding.text_id),
            **embedding._asdict()
        )

    async def find_by_id(self, id: int) -> Optional[Embedding]:
        stmt = select(
            "*").select_from(EmbeddingTable).where(EmbeddingTable.c.id == id)
        result = await self.connection_provider.get_current_connection().execute(stmt)
        embedding = result.first()
        if not embedding:
            return None
        return Embedding(
            text=OneToOne[MyText](id=embedding.text_id),
            **embedding._asdict()
        )

    async def list(self, size: int, page: int) -> ListResult[Embedding]:
        total_stmt = select(count()).select_from(EmbeddingTable)
        total = (await self.connection_provider.get_current_connection().execute(total_stmt)).scalar()

        stmt = (
            select("*")
            .select_from(EmbeddingTable)
            .order_by(desc(EmbeddingTable.c.id))
            .offset((page - 1) * size)
            .limit(size)
        )

        result = await self.connection_provider.get_current_connection().execute(stmt)
        return ListResult[Embedding](
            items=[
                Embedding(
                    text=OneToOne[MyText](id=row.text_id),
                    **row._asdict()
                )
                for row in result.all()
            ],
            total=total
        )

    async def update(self, entity: Embedding) -> Embedding:
        pass

    async def delete(self, id: int) -> None:
        await self.connection_provider.get_current_connection().execute(
            delete(EmbeddingTable).where(EmbeddingTable.c.id == id)
        )
