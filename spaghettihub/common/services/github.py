import uuid
from datetime import datetime
from typing import Optional

from temporalio.client import Client

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.db.github import LaunchpadToGithubWorkRepository
from spaghettihub.common.models.github import LaunchpadToGithubWork
from spaghettihub.common.services.base import Service
from spaghettihub.common.workflows.constants import TASK_QUEUE_NAME
from spaghettihub.common.workflows.launchpad_to_github.params import \
    TemporalLaunchpadToGithubParams


class LaunchpadToGithubWorkService(Service):

    def __init__(
            self,
            connection_provider: ConnectionProvider,
            launchpad_to_github_work_repository: LaunchpadToGithubWorkRepository,
            temporal_client: Client | None = None
    ):
        super().__init__(connection_provider)
        self.launchpad_to_github_work_repository = launchpad_to_github_work_repository
        self.temporal_client = temporal_client

    async def create(self, launchpad_url: str) -> LaunchpadToGithubWork:
        request_uuid = str(uuid.uuid4())
        work = await self.launchpad_to_github_work_repository.create(
            LaunchpadToGithubWork(
                id=await self.launchpad_to_github_work_repository.get_next_id(),
                requested_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                status="NEW",
                request_uuid=request_uuid,
                launchpad_url=launchpad_url
            )
        )

        await self.temporal_client.start_workflow(
            "launchpad-to-github-workflow",
            TemporalLaunchpadToGithubParams(
                request_uuid=request_uuid,
                merge_proposal_link=launchpad_url
            ),
            id="launchpad-to-github-workflow-" + request_uuid,
            task_queue=TASK_QUEUE_NAME,
        )

        return work

    async def get(self, request_uuid: str) -> Optional[LaunchpadToGithubWork]:
        return await self.launchpad_to_github_work_repository.find_by_request_uuid(request_uuid)

    async def finish(self, request_uuid: str, github_url: str, status: str) -> LaunchpadToGithubWork:
        work = await self.get(request_uuid)
        now = datetime.utcnow()
        work.completed_at = now
        work.updated_at = now
        work.status = status
        work.github_url = github_url
        return await self.launchpad_to_github_work_repository.update(work)
