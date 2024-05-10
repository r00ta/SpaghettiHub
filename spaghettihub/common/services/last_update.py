from datetime import datetime
from typing import Optional

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.db.last_update import LastUpdateRepository
from spaghettihub.common.models.last_update import LastUpdate
from spaghettihub.common.services.base import Service


class LastUpdateService(Service):

    ROW_ID = 1

    def __init__(
        self,
        connection_provider: ConnectionProvider,
        last_update_repository: LastUpdateRepository,
    ):
        super().__init__(connection_provider)
        self.last_update_repository = last_update_repository

    async def get_last_update(self) -> Optional[LastUpdate]:
        return await self.last_update_repository.find_by_id(self.ROW_ID)

    async def set_last_update(self, time: datetime) -> None:
        last_update = await self.get_last_update()
        if not last_update:
            return await self.last_update_repository.create(
                LastUpdate(id=self.ROW_ID, last_updated=time)
            )
        last_update.last_updated = time
