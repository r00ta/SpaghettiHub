from datetime import datetime

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.db.merge_proposals import MergeProposalsRepository
from spaghettihub.common.models.base import ListResult
from spaghettihub.common.models.merge_proposals import MergeProposal
from spaghettihub.common.services.base import Service


class MergeProposalsService(Service):

    def __init__(
            self,
            connection_provider: ConnectionProvider,
            merge_proposals_repository: MergeProposalsRepository,
    ):
        super().__init__(connection_provider)
        self.merge_proposals_repository = merge_proposals_repository

    async def create(self,
                     commit_message: str | None,
                     date_merged: datetime,
                     source_git_path: str | None,
                     target_git_path: str | None,
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
