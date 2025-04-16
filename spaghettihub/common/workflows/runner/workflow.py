import logging
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from spaghettihub.common.models.runner import GithubPushWebhook, GithubWebhook, WorkflowJob, WorkflowAction
from spaghettihub.common.workflows.constants import TASK_QUEUE_NAME
from spaghettihub.common.workflows.runner.params import TemporalGithubRunnerWorkflowParams, SpawnVirtualMachineActivityParams

with workflow.unsafe.imports_passed_through():
    pass

WORK_DIR = "/home/ubuntu/.spaghettihub/"

log = logging.getLogger()

@workflow.defn(name="handle-github-push-webhook-workflow", sandboxed=False)
class GithubPushWebhookWorkflow:
    @workflow.run
    async def run(self, request: GithubPushWebhook) -> None:
        await workflow.execute_activity(
            "update-commit-metadata",
            request,
            start_to_close_timeout=timedelta(seconds=120),
            heartbeat_timeout=timedelta(seconds=5),
            retry_policy=RetryPolicy(maximum_attempts=5)
        )

@workflow.defn(name="handle-github-workflow-webhook-workflow", sandboxed=False)
class GithubWorkflowWebhookRunnerWorkflow:

    def is_continuous_deliver_pipeline(self, workflow: WorkflowJob):
        return "Continuous delivery" == workflow.workflow_name and "master" == workflow.head_branch

    @workflow.run
    async def run(self, request: GithubWebhook) -> None:
        # Specific handling for this job triggered when something has been pushed to main
        if self.is_continuous_deliver_pipeline(request.workflow_job):
            await workflow.execute_activity(
                "update-continuous-delivery-commit-metadata",
                request,
                start_to_close_timeout=timedelta(seconds=120),
                heartbeat_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(maximum_attempts=5)
            )

        if "self-hosted" not in request.workflow_job.labels:
            return

        if request.action == WorkflowAction.queued:
            await workflow.execute_child_workflow(
                "github-runner-workflow",
                TemporalGithubRunnerWorkflowParams(
                    id=request.workflow_job.id,
                    run_url=request.workflow_job.run_url,
                    labels=request.workflow_job.labels,
                ),
                id="github-runner-workflow-" + str(request.workflow_job.id),
                task_queue=TASK_QUEUE_NAME,
                retry_policy=RetryPolicy(maximum_attempts=1),
                execution_timeout=timedelta(hours=12)
            )
        elif request.action == WorkflowAction.completed:
            # The runner name is the id of the workflow that handled the workload.
            hdl = workflow.get_external_workflow_handle(workflow_id="internal-github-runner-workflow-" + str(request.workflow_job.runner_name))
            try:
                await hdl.signal("completed")
                log.info(f"Workflow {str(request.workflow_job.id)} signal completed")
            except:
                log.warning(f"Could not signal the workflow {str(request.workflow_job.id)}")

@workflow.defn(name="github-runner-workflow", sandboxed=False)
class TemporalGithubRunnerWorkflow:
    @workflow.run
    async def run(self, params: TemporalGithubRunnerWorkflowParams) -> None:
        try:
            return await workflow.execute_child_workflow(
                "internal-github-runner-workflow",
                params,
                id="internal-github-runner-workflow-" + str(params.id),
                task_queue=TASK_QUEUE_NAME,
                retry_policy=RetryPolicy(maximum_attempts=1),
                execution_timeout=timedelta(hours=5)
            )
        except Exception:
            await workflow.execute_activity(
                "destroy-runner",
                params.id,
                start_to_close_timeout=timedelta(seconds=60),
                heartbeat_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=1)
            )


@workflow.defn(name="internal-github-runner-workflow", sandboxed=False)
class TemporalInternalGithubRunnerWorkflow:
    def __init__(self) -> None:
        self._completed = False

    @workflow.signal(name="completed")
    async def signal_completed(self, *args: list[Any]) -> None:
        self._completed = True

    @workflow.run
    async def run(self, params: TemporalGithubRunnerWorkflowParams) -> None:
        registration_token = await workflow.execute_activity(
            "get-registration-token",
            start_to_close_timeout=timedelta(seconds=60),
            heartbeat_timeout=timedelta(seconds=60)
        )

        await workflow.execute_activity(
            "spawn-runner",
            SpawnVirtualMachineActivityParams(
                id=params.id,
                labels=params.labels,
                registration_token=registration_token
            ),
            start_to_close_timeout=timedelta(seconds=120),
            heartbeat_timeout=timedelta(seconds=120)
        )

        await workflow.wait_condition(lambda: self._completed)

        await workflow.execute_activity(
            "destroy-runner",
            params.id,
            start_to_close_timeout=timedelta(seconds=120),
            heartbeat_timeout=timedelta(seconds=120)
        )
