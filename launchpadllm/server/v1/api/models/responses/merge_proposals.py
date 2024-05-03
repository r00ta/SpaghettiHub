from datetime import datetime

from pydantic import BaseModel

from launchpadllm.common.models.merge_proposals import MergeProposal
from launchpadllm.server.v1.api.models.responses.base import (
    BaseResponse, PaginatedResponse)


class MergeProposalResponse(BaseResponse):
    kind: str = "MergeProposal"
    id: int
    commit_message: str | None
    date_merged: datetime
    source_git_path: str
    target_git_path: str
    registrant_name: str
    web_link: str

    @staticmethod
    def from_model(entity: MergeProposal) -> "MergeProposalResponse":
        response = MergeProposalResponse(
            id=entity.id,
            commit_message=entity.commit_message,
            date_merged=entity.date_merged,
            source_git_path=entity.source_git_path,
            target_git_path=entity.target_git_path,
            registrant_name=entity.registrant_name,
            web_link=entity.web_link
        )
        return response


class MergeProposalsListResponse(PaginatedResponse[MergeProposalResponse]):
    kind: str = "MergeProposalsList"
