from typing import Optional

from sqlalchemy import delete, desc, insert, select
from sqlalchemy.sql.functions import count

from spaghettihub.common.db.repository import BaseRepository
from spaghettihub.common.db.sequences import (MergeProposalsSequence)
from spaghettihub.common.db.tables import (MergeProposalTable)
from spaghettihub.common.models.base import ListResult
from spaghettihub.common.models.merge_proposals import MergeProposal
from spaghettihub.common.models.texts import MyText


class MergeProposalsRepository(BaseRepository[MergeProposal]):
    async def get_next_id(self) -> int:
        stmt = select(MergeProposalsSequence.next_value())
        return (
            await self.connection_provider.get_current_connection().execute(stmt)
        ).scalar()

    async def create(self, entity: MergeProposal) -> MergeProposal:
        stmt = (
            insert(MergeProposalTable)
            .returning(
                MergeProposalTable.c.id,
                MergeProposalTable.c.commit_message,
                MergeProposalTable.c.date_merged,
                MergeProposalTable.c.source_git_path,
                MergeProposalTable.c.target_git_path,
                MergeProposalTable.c.registrant_name,
                MergeProposalTable.c.web_link,
            )
            .values(
                id=entity.id,
                commit_message=entity.commit_message,
                date_merged=entity.date_merged,
                source_git_path=entity.source_git_path,
                target_git_path=entity.target_git_path,
                registrant_name=entity.registrant_name,
                web_link=entity.web_link,
            )
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        text = result.one()
        return MergeProposal(**text._asdict())

    async def find_by_id(self, id: int) -> Optional[MergeProposal]:
        stmt = select(
            "*").select_from(MergeProposalTable).where(MergeProposalTable.c.id == id)
        result = await self.connection_provider.get_current_connection().execute(stmt)
        text = result.first()
        if not text:
            return None
        return MergeProposal(**text._asdict())

    async def find_by_commit_message_match(self, message: str, page: int, size: int) -> ListResult[MergeProposal]:
        """
        More recent MPs first.
        """

        total_stmt = select(count()).select_from(MergeProposalTable).where(
            MergeProposalTable.c.commit_message.like("%" + message + "%"))
        total = (await self.connection_provider.get_current_connection().execute(total_stmt)).scalar()

        stmt = (
            select("*")
            .select_from(MergeProposalTable)
            .where(MergeProposalTable.c.commit_message.like("%" + message + "%"))
            .order_by(desc(MergeProposalTable.c.date_merged))
            .offset((page - 1) * size)
            .limit(size)
        )

        result = await self.connection_provider.get_current_connection().execute(stmt)
        return ListResult[MergeProposal](
            items=[MergeProposal(**row._asdict()) for row in result.all()],
            total=total
        )

    async def list(self, size: int, page: int) -> ListResult[MergeProposal]:
        pass

    async def update(self, entity: MyText) -> MyText:
        pass

    async def delete(self, id: int) -> None:
        await self.connection_provider.get_current_connection().execute(
            delete(MergeProposalTable).where(MergeProposalTable.c.id == id)
        )
