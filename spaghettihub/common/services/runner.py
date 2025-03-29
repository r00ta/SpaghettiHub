import hashlib
import hmac
import logging

from temporalio.client import Client
from temporalio.service import RPCError

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.models.runner import GithubWebhook, WorkflowAction
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
            webhook_secret: str,
    ):
        super().__init__(connection_provider)
        self.webhook_secret = webhook_secret

    async def process_webhook(self, request: GithubWebhook):
        if request.action == WorkflowAction.queued:
            if "self-hosted" not in request.workflow_job.labels:
                return

            client = await Client.connect("localhost:7233")

            await client.start_workflow(
                "github-runner-workflow",
                TemporalGithubRunnerWorkflowParams(
                    run_id=request.workflow_job.run_id,
                    run_url=request.workflow_job.run_url,
                    labels=request.workflow_job.labels,
                ),
                id="github-runner-workflow-" + str(request.workflow_job.run_id),
                task_queue=TASK_QUEUE_NAME,
            )
            log.info(f"New runner workflow {str(request.workflow_job.run_id)}")
        elif request.action == WorkflowAction.completed:
            if "self-hosted" not in request.workflow_job.labels:
                return

            client = await Client.connect("localhost:7233")

            # The runner name is the run_id of the workflow that handled the workload.
            hdl = client.get_workflow_handle("internal-github-runner-workflow-" + str(request.workflow_job.runner_name))
            try:
                await hdl.signal("completed")
                log.info(f"Workflow {str(request.workflow_job.run_id)} has been signaled")
            except RPCError:
                log.warning(f"Could not signal the workflow {str(request.workflow_job.run_id)}")

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
