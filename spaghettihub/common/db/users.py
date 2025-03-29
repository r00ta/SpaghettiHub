from typing import Optional

from sqlalchemy import delete, insert, select

from spaghettihub.common.db.repository import BaseRepository
from spaghettihub.common.db.sequences import (UsersSequence)
from spaghettihub.common.db.tables import (UserTable)
from spaghettihub.common.models.base import ListResult
from spaghettihub.common.models.github import LaunchpadToGithubWork
from spaghettihub.common.models.users import User


class UsersRepository(BaseRepository[User]):
    async def get_next_id(self) -> int:
        stmt = select(UsersSequence.next_value())
        return (
            await self.connection_provider.get_current_connection().execute(stmt)
        ).scalar()

    async def create(self, entity: User) -> User:
        stmt = (
            insert(UserTable)
            .returning(
                UserTable.c.id,
                UserTable.c.username,
                UserTable.c.password
            )
            .values(
                id=entity.id,
                username=entity.username,
                password=entity.password
            )
        )
        result = await self.connection_provider.get_current_connection().execute(stmt)
        row = result.one()
        return User(**row._asdict())

    async def find_by_id(self, id: int) -> Optional[User]:
        stmt = select("*").select_from(UserTable).where(UserTable.c.id == id)
        result = await self.connection_provider.get_current_connection().execute(stmt)
        user = result.first()
        if not user:
            return None
        return User(**user._asdict())

    async def find_by_username(self, username: str) -> Optional[User]:
        stmt = select(
            "*").select_from(UserTable).where(UserTable.c.username == username)
        result = await self.connection_provider.get_current_connection().execute(stmt)
        user = result.first()
        if not user:
            return None
        return User(**user._asdict())

    async def list(self, size: int, page: int) -> ListResult[LaunchpadToGithubWork]:
        pass

    async def update(self, entity: LaunchpadToGithubWork) -> LaunchpadToGithubWork:
        pass

    async def delete(self, id: str) -> None:
        await self.connection_provider.get_current_connection().execute(
            delete(UserTable).where(UserTable.c.id == id)
        )
