from typing import Optional

from sqlalchemy import delete, insert, select

from launchpadllm.common.db.repository import BaseRepository
from launchpadllm.common.db.sequences import BugCommentSequence
from launchpadllm.common.db.tables import BugCommentTable, BugTable
from launchpadllm.common.models.base import ListResult
from launchpadllm.common.models.bugs import Bug, BugComment


class BugsRepository(BaseRepository[Bug]):
    async def get_next_id(self) -> int:
        raise Exception("not implemented")

    async def get_next_comment_id(self) -> int:
        stmt = select(BugCommentSequence.next_value())
        return (
            await self.connection_provider.get_current_connection().execute(stmt)
        ).scalar()

    async def create(self, entity: Bug) -> Bug:
        stmt = (
            insert(BugTable)
            .returning(
                BugTable.c.id,
                BugTable.c.date_created,
                BugTable.c.date_last_updated,
                BugTable.c.web_link,
                BugTable.c.title_id,
                BugTable.c.description_id,
            )
            .values(
                id=entity.id,
                date_created=entity.date_created,
                date_last_updated=entity.date_last_updated,
                web_link=entity.web_link,
                title_id=entity.title_id,
                description_id=entity.description_id,
            )
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        bug = result.one()
        return Bug(**bug._asdict())

    async def find_by_id(self, id: int) -> Optional[Bug]:
        stmt = select("*").select_from(BugTable).where(BugTable.c.id == id)
        result = await self.connection_provider.get_current_connection().execute(stmt)
        bug = result.first()
        if not bug:
            return None
        return Bug(**bug._asdict())

    async def list(self, size: int, page: int) -> ListResult[Bug]:
        pass

    async def update(self, entity: Bug) -> Bug:
        pass

    async def delete(self, id: int) -> None:
        await self.connection_provider.get_current_connection().execute(
            delete(BugTable).where(BugTable.c.id == id)
        )

    async def delete_comments(self, id: int) -> None:
        # embeddings and texts are cascaded
        await self.connection_provider.get_current_connection().execute(
            delete(BugCommentTable).where(BugCommentTable.c.bug_id == id)
        )

    async def add_comment(self, entity: BugComment) -> BugComment:
        stmt = (
            insert(BugCommentTable)
            .returning(
                BugCommentTable.c.id,
                BugCommentTable.c.text_id,
                BugCommentTable.c.bug_id,
            )
            .values(
                id=entity.id,
                text_id=entity.text_id,
                bug_id=entity.bug_id,
            )
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        bug_comment = result.one()
        return BugComment(**bug_comment._asdict())
