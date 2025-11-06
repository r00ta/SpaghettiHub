from fastapi import Depends
from pydantic import BaseModel

from spaghettihub.common.services.collection import ServiceCollection
from spaghettihub.server.base.api.base import Handler, handler
from spaghettihub.server.v1.api import authenticated, services


class MirrorPRCommentsRequest(BaseModel):
    github_pr_url: str
    launchpad_mp_url: str
    include_outdated: bool = False
    include_review_states: bool = False


class MirrorPRCommentsResponse(BaseModel):
    workflow_id: str
    status: str


class MirrorPRCommentsHandler(Handler):
    """Handler for mirroring PR comments to Launchpad MP."""

    TAGS = ["Mirror PR Comments"]

    @handler(
        path="/tools/mirror-pr-comments",
        methods=["POST"],
        tags=TAGS,
        response_model=MirrorPRCommentsResponse,
        response_model_exclude_none=True,
        status_code=202,
        dependencies=[Depends(authenticated)]
    )
    async def mirror_pr_comments(
            self,
            request: MirrorPRCommentsRequest,
            services: ServiceCollection = Depends(services)
    ) -> MirrorPRCommentsResponse:
        """
        Start a workflow to mirror comments from a GitHub PR to a Launchpad MP.
        """
        workflow_id = await services.mirror_comments_service.start_mirror(
            github_pr_url=request.github_pr_url,
            launchpad_mp_url=request.launchpad_mp_url,
            include_outdated=request.include_outdated,
            include_review_states=request.include_review_states,
        )

        return MirrorPRCommentsResponse(
            workflow_id=workflow_id,
            status="started"
        )
