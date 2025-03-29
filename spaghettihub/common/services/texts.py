from typing import List

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.db.texts import TextsRepository
from spaghettihub.common.models.texts import MyText
from spaghettihub.common.services.base import Service


class TextsService(Service):

    def __init__(
            self, connection_provider: ConnectionProvider, texts_repository: TextsRepository
    ):
        super().__init__(connection_provider)
        self.texts_repository = texts_repository

    async def create(self, text: str) -> MyText:
        return await self.texts_repository.create(
            MyText(id=await self.texts_repository.get_next_id(), content=text)
        )

    async def delete(self, id: int) -> None:
        return await self.texts_repository.delete(id)

    async def find_texts_without_embeddings(self) -> List[MyText]:
        return await self.texts_repository.find_texts_without_embeddings()
