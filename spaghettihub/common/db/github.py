from typing import List, Optional

from sqlalchemy import delete, insert, select, update
from sqlalchemy.sql.operators import eq, or_

from spaghettihub.common.db.repository import BaseRepository
from spaghettihub.common.db.sequences import (BugCommentSequence,
                                              LaunchpadToGithubWorkSequence)
from spaghettihub.common.db.tables import (BugCommentTable, BugTable,
                                           LaunchpadToGithubWorkTable,
                                           MyTextTable)
from spaghettihub.common.models.base import ListResult
from spaghettihub.common.models.bugs import Bug, BugComment
from spaghettihub.common.models.github import LaunchpadToGithubWork
from spaghettihub.common.models.texts import MyText


class LaunchpadToGithubWorkRepository(BaseRepository[LaunchpadToGithubWork]):
    async def get_next_id(self) -> int:
        stmt = select(LaunchpadToGithubWorkSequence.next_value())
        return (
            await self.connection_provider.get_current_connection().execute(stmt)
        ).scalar()

    async def create(self, entity: LaunchpadToGithubWork) -> LaunchpadToGithubWork:
        stmt = (
            insert(LaunchpadToGithubWorkTable)
            .returning(
                LaunchpadToGithubWorkTable.c.id,
                LaunchpadToGithubWorkTable.c.requested_at,
                LaunchpadToGithubWorkTable.c.updated_at,
                LaunchpadToGithubWorkTable.c.completed_at,
                LaunchpadToGithubWorkTable.c.request_uuid,
                LaunchpadToGithubWorkTable.c.status,
                LaunchpadToGithubWorkTable.c.github_url,
                LaunchpadToGithubWorkTable.c.launchpad_url,
            )
            .values(
                id=entity.id,
                requested_at=entity.requested_at,
                updated_at=entity.updated_at,
                completed_at=entity.completed_at,
                request_uuid=entity.request_uuid,
                status=entity.status,
                github_url=entity.github_url,
                launchpad_url=entity.launchpad_url
            )
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        row = result.one()
        return LaunchpadToGithubWork(**row._asdict())

    async def find_by_id(self, id: int) -> Optional[LaunchpadToGithubWork]:
        stmt = select(
            "*").select_from(LaunchpadToGithubWorkTable).where(LaunchpadToGithubWorkTable.c.id == id)
        result = await self.connection_provider.get_current_connection().execute(stmt)
        bug = result.first()
        if not bug:
            return None
        return LaunchpadToGithubWork(**bug._asdict())

    async def find_by_request_uuid(self, request_uuid: str) -> Optional[LaunchpadToGithubWork]:
        stmt = select("*").select_from(LaunchpadToGithubWorkTable).where(
            LaunchpadToGithubWorkTable.c.request_uuid == request_uuid)
        result = await self.connection_provider.get_current_connection().execute(stmt)
        work = result.first()
        if not work:
            return None
        return LaunchpadToGithubWork(**work._asdict())

    async def list(self, size: int, page: int) -> ListResult[LaunchpadToGithubWork]:
        pass

    async def update(self, entity: LaunchpadToGithubWork) -> LaunchpadToGithubWork:
        stmt = (
            update(LaunchpadToGithubWorkTable)
            .where(LaunchpadToGithubWorkTable.c.id == entity.id)
            .values(**entity.dict())
        )
        await self.connection_provider.get_current_connection().execute(stmt)
        return entity

    async def delete(self, id: str) -> None:
        await self.connection_provider.get_current_connection().execute(
            delete(LaunchpadToGithubWorkTable).where(
                LaunchpadToGithubWorkTable.c.id == id)
        )
