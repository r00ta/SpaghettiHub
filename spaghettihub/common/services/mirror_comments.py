import hashlib
from typing import Optional

from temporalio.client import Client

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.db.mirrored_comments import MirroredCommentsRepository
from spaghettihub.common.services.base import Service
from spaghettihub.common.workflows.constants import TASK_QUEUE_NAME
from spaghettihub.common.workflows.mirror_pr_comments.params import (
    MirrorCommentsResult, MirrorPullRequestCommentsParams)


class MirrorCommentsService(Service):

    def __init__(
            self,
            connection_provider: ConnectionProvider,
            mirrored_comments_repository: MirroredCommentsRepository,
            temporal_client: Client | None = None
    ):
        super().__init__(connection_provider)
        self.mirrored_comments_repository = mirrored_comments_repository
        self.temporal_client = temporal_client

    async def start_mirror(
        self,
        github_pr_url: str,
        launchpad_mp_url: str,
        include_outdated: bool = False,
        include_review_states: bool = False,
    ) -> str:
        """Start a workflow to mirror PR comments to Launchpad MP."""
        # Generate unique workflow ID
        workflow_id_content = f"{github_pr_url}:{launchpad_mp_url}"
        workflow_hash = hashlib.sha256(
            workflow_id_content.encode()).hexdigest()[:16]
        workflow_id = f"mirror-pr-comments-{workflow_hash}"

        params = MirrorPullRequestCommentsParams(
            github_pr_url=github_pr_url,
            launchpad_mp_url=launchpad_mp_url,
            include_outdated=include_outdated,
            include_review_states=include_review_states,
        )

        await self.temporal_client.start_workflow(
            "mirror-pr-comments-workflow",
            params,
            id=workflow_id,
            task_queue=TASK_QUEUE_NAME,
        )

        return workflow_id
