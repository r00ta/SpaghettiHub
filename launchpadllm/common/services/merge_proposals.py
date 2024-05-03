from datetime import datetime
from typing import List, Optional

from launchpadllm.common.db.base import ConnectionProvider
from launchpadllm.common.db.last_update import LastUpdateRepository
from launchpadllm.common.db.merge_proposals import MergeProposalsRepository
from launchpadllm.common.models.base import ListResult
from launchpadllm.common.models.last_update import LastUpdate
from launchpadllm.common.models.merge_proposals import MergeProposal
from launchpadllm.common.services.base import Service


class MergeProposalsService(Service):

    def __init__(
        self,
        connection_provider: ConnectionProvider,
        merge_proposals_repository: MergeProposalsRepository,
    ):
        super().__init__(connection_provider)
        self.merge_proposals_repository = merge_proposals_repository

    async def create(self,
                     commit_message: str,
                     date_merged: datetime,
                     source_git_path: str,
                     target_git_path: str,
                     registrant_name: str,
                     web_link: str):
        await self.merge_proposals_repository.create(
            MergeProposal(
                id=await self.merge_proposals_repository.get_next_id(),
                commit_message=commit_message,
                date_merged=date_merged,
                source_git_path=source_git_path,
                target_git_path=target_git_path,
                registrant_name=registrant_name,
                web_link=web_link
            )
        )

    async def find_merge_proposals_contain_message(self, message: str, page: int, size: int) -> ListResult[MergeProposal]:
        return await self.merge_proposals_repository.find_by_commit_message_match(message, page, size)
