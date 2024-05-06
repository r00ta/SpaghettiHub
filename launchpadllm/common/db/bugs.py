from typing import List, Optional

from sqlalchemy import delete, insert, select
from sqlalchemy.sql.operators import eq, or_

from launchpadllm.common.db.repository import BaseRepository
from launchpadllm.common.db.sequences import BugCommentSequence
from launchpadllm.common.db.tables import (BugCommentTable, BugTable,
                                           MyTextTable)
from launchpadllm.common.models.base import ListResult
from launchpadllm.common.models.bugs import Bug, BugComment
from launchpadllm.common.models.texts import MyText


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

    async def find_by_text_id(self, id: int) -> Optional[Bug]:
        title_cte = (
            select(
                BugTable.c.id,
                BugTable.c.title_id,
                MyTextTable.c.content
            )
            .select_from(BugTable)
            .join(
                MyTextTable,
                MyTextTable.c.id == BugTable.c.title_id,
            )
        ).cte("title_cte")

        description_cte = (
            select(
                BugTable.c.id,
                BugTable.c.description_id,
                MyTextTable.c.content
            )
            .select_from(BugTable)
            .join(
                MyTextTable,
                MyTextTable.c.id == BugTable.c.description_id,
            )
        ).cte("description_cte")

        stmt = (select(
            BugTable.c.id,
            BugTable.c.date_created,
            BugTable.c.date_last_updated,
            BugTable.c.web_link,
            BugTable.c.title_id,
            title_cte.c.content.label("title_content"),
            BugTable.c.description_id,
            description_cte.c.content.label("description_content")
        )
            .select_from(BugTable)
            .join(BugCommentTable,
                  BugCommentTable.c.bug_id == BugTable.c.id,
                  isouter=True)
            .join(
            title_cte,
            title_cte.c.id == BugTable.c.id, isouter=True
        )
            .join(
            description_cte,
            description_cte.c.id == BugTable.c.id, isouter=True
        )
            .where(
            (BugTable.c.title_id == id) |
            (BugTable.c.description_id == id) |
            (BugCommentTable.c.text_id == id)
        )
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        bug = result.first()
        if not bug:
            return None
        return Bug(
            title=MyText(id=bug.title_id, content=bug.title_content),
            description=MyText(id=bug.description_id,
                               content=bug.description_content),
            **bug._asdict()
        )

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

    async def find_bug_comments(self, bug_id: int) -> List[BugComment]:
        stmt = (select(
            BugCommentTable.c.id,
            BugCommentTable.c.text_id,
            BugCommentTable.c.bug_id,
            MyTextTable.c.content
        )
            .select_from(BugCommentTable)
            .join(
            MyTextTable,
            MyTextTable.c.id == BugCommentTable.c.text_id
        )
            .where(
            BugCommentTable.c.bug_id == bug_id,
        )
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        return [BugComment(
                text=MyText(id=bug_comment.id, content=bug_comment.content),
                **bug_comment._asdict()) for bug_comment in result.all()]
