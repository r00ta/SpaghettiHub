from typing import List, Optional

from sqlalchemy import insert, select
from sqlalchemy.sql.functions import count

from spaghettihub.common.db.repository import BaseRepository
from spaghettihub.common.db.sequences import MirroredCommentSequence
from spaghettihub.common.db.tables import MirroredCommentTable
from spaghettihub.common.models.base import ListResult
from spaghettihub.common.models.mirrored_comments import MirroredComment


class MirroredCommentsRepository(BaseRepository[MirroredComment]):
    async def get_next_id(self) -> int:
        stmt = select(MirroredCommentSequence.next_value())
        return (
            await self.connection_provider.get_current_connection().execute(stmt)
        ).scalar()

    async def create(self, entity: MirroredComment) -> MirroredComment:
        stmt = (
            insert(MirroredCommentTable)
            .returning(
                MirroredCommentTable.c.id,
                MirroredCommentTable.c.fingerprint,
                MirroredCommentTable.c.github_comment_id,
                MirroredCommentTable.c.github_source,
                MirroredCommentTable.c.mp_identifier,
                MirroredCommentTable.c.created_at,
                MirroredCommentTable.c.posted_at,
                MirroredCommentTable.c.status,
                MirroredCommentTable.c.error_message,
            )
            .values(
                id=entity.id,
                fingerprint=entity.fingerprint,
                github_comment_id=entity.github_comment_id,
                github_source=entity.github_source,
                mp_identifier=entity.mp_identifier,
                created_at=entity.created_at,
                posted_at=entity.posted_at,
                status=entity.status,
                error_message=entity.error_message,
            )
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        row = result.one()
        return MirroredComment(**row._asdict())

    async def find_by_fingerprint(self, fingerprint: str) -> Optional[MirroredComment]:
        stmt = select("*").select_from(MirroredCommentTable).where(
            MirroredCommentTable.c.fingerprint == fingerprint
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        row = result.first()
        if not row:
            return None
        return MirroredComment(**row._asdict())

    async def find_by_mp_identifier(self, mp_identifier: str) -> List[MirroredComment]:
        stmt = select("*").select_from(MirroredCommentTable).where(
            MirroredCommentTable.c.mp_identifier == mp_identifier
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        return [MirroredComment(**row._asdict()) for row in result.all()]

    async def find_by_id(self, id: int) -> Optional[MirroredComment]:
        stmt = select("*").select_from(MirroredCommentTable).where(
            MirroredCommentTable.c.id == id
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        row = result.first()
        if not row:
            return None
        return MirroredComment(**row._asdict())

    async def list(self, size: int, page: int) -> ListResult[MirroredComment]:
        pass

    async def update(self, entity: MirroredComment) -> MirroredComment:
        pass

    async def delete(self, id: int) -> None:
        pass
