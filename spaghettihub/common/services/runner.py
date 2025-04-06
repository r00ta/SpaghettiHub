import hashlib
import hmac
import logging

from temporalio.client import Client
from temporalio.service import RPCError

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.db.maas import MAASRepository
from spaghettihub.common.models.maas import MAAS
from spaghettihub.common.models.runner import GithubWebhook, WorkflowAction, GithubPushWebhook, WorkflowJob
from spaghettihub.common.services.base import Service
from spaghettihub.common.workflows.constants import TASK_QUEUE_NAME
from spaghettihub.common.workflows.runner.params import TemporalGithubRunnerWorkflowParams

log = logging.getLogger()


class InvalidWebhook(Exception):
    """ Invalid webhook """


class GithubWorkflowRunnerService(Service):

    def __init__(
            self,
            connection_provider: ConnectionProvider,
            maas_repository: MAASRepository,
            webhook_secret: str,
    ):
        super().__init__(connection_provider)
        self.webhook_secret = webhook_secret
        self.maas_repository = maas_repository

    def is_continuous_deliver_pipeline(self, workflow: WorkflowJob):
        return "Continuous delivery pipeline" == workflow.workflow_name and "master" == workflow.head_branch

    async def list_commits(self, query: str | None, page: int, size: int):
        return await self.maas_repository.list_commits(query, page, size)

    async def list(self, page: int, size: int):
        pass

    async def process_push_webhook(self, request: GithubPushWebhook):
        if request.ref != "refs/heads/master":
            return

        # Should not happen, but it might be that the workflow job was processed before.
        maas = await self.maas_repository.find_by_sha(request.head_commit.id)
        if maas is not None:
            maas.commit_sha = request.head_commit.id,
            maas.commit_message = request.head_commit.message,
            maas.committer_username = request.head_commit.author.username,
            maas.commit_date = request.head_commit.timestamp
            await self.maas_repository.update(maas)
        else:
            await self.maas_repository.create(
                MAAS(
                    id=await self.maas_repository.get_next_id(),
                    commit_sha=request.head_commit.id,
                    commit_message=request.head_commit.message,
                    committer_username=request.head_commit.author.username,
                    commit_date=request.head_commit.timestamp,
                )
            )

    async def process_webhook(self, request: GithubWebhook):
        # Specific handling for this job triggered when something has been pushed to main
        if self.is_continuous_deliver_pipeline(request.workflow_job):
            maas = await self.maas_repository.find_by_sha(request.workflow_job.head_sha)
            if maas is None:
                log.warning(f"Could not find commit with sha {request.workflow_job.head_sha}. Creating it")
            maas = MAAS(
                id=await self.maas_repository.get_next_id(),
                commit_sha=request.workflow_job.head_sha,
                commit_message=None,
                committer_username=None,
                commit_date=None,
            )
            if request.workflow_job.name == "deb":
                maas.continuous_delivery_test_deb_status = request.workflow_job.conclusion
            elif request.workflow_job.name == "snap":
                maas.continuous_delivery_test_snap_status = request.workflow_job.conclusion
            await self.maas_repository.update(maas)

        if request.action == WorkflowAction.queued:
            if "self-hosted" not in request.workflow_job.labels:
                return

            client = await Client.connect("localhost:7233")

            await client.start_workflow(
                "github-runner-workflow",
                TemporalGithubRunnerWorkflowParams(
                    id=request.workflow_job.id,
                    run_url=request.workflow_job.run_url,
                    labels=request.workflow_job.labels,
                ),
                id="github-runner-workflow-" + str(request.workflow_job.id),
                task_queue=TASK_QUEUE_NAME,
            )
            log.info(f"New runner workflow {str(request.workflow_job.id)}")
        elif request.action == WorkflowAction.completed:
            if "self-hosted" not in request.workflow_job.labels:
                return

            client = await Client.connect("localhost:7233")

            # The runner name is the id of the workflow that handled the workload.
            hdl = client.get_workflow_handle("internal-github-runner-workflow-" + str(request.workflow_job.runner_name))
            try:
                await hdl.signal("completed")
                log.info(f"Workflow {str(request.workflow_job.id)} has been signaled")
            except RPCError:
                log.warning(f"Could not signal the workflow {str(request.workflow_job.id)}")

    def verify_signature(self, payload_body, signature_header):
        """Verify that the payload was sent from GitHub by validating SHA256.

        Raise and return 403 if not authorized.

        Args:
            payload_body: original request body to verify (request.body())
            secret_token: GitHub app webhook token (WEBHOOK_SECRET)
            signature_header: header received from GitHub (x-hub-signature-256)
        """
        if not signature_header:
            raise InvalidWebhook("x-hub-signature-256 header is missing!")
        hash_object = hmac.new(self.webhook_secret.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
        expected_signature = "sha256=" + hash_object.hexdigest()
        if not hmac.compare_digest(expected_signature, signature_header):
            raise InvalidWebhook("Request signatures didn't match!")
