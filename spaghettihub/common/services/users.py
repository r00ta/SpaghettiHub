import hashlib
from typing import Optional

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.db.users import UsersRepository
from spaghettihub.common.models.users import User
from spaghettihub.common.services.base import Service


class UsersService(Service):

    def __init__(
            self,
            connection_provider: ConnectionProvider,
            users_repository: UsersRepository
    ):
        super().__init__(connection_provider)
        self.users_repository = users_repository

    def _hash_password(self, password: str) -> str:
        t_sha = hashlib.sha512()
        t_sha.update(password.encode())
        return t_sha.hexdigest()

    async def login(self, username: str, password: str) -> Optional[User]:
        user = await self.users_repository.find_by_username(username)
        print(user)
        if user and user.password == self._hash_password(password):
            return user
        return None

    async def create(self, username: str, password: str) -> User:
        return await self.users_repository.create(
            User(
                id=await self.users_repository.get_next_id(),
                username=username,
                password=self._hash_password(password)
            )
        )
