from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from spaghettihub.common.workflows.constants import TASK_QUEUE_NAME
from spaghettihub.common.workflows.runner.params import TemporalGithubRunnerWorkflowParams, SpawnVirtualMachineActivityParams

with workflow.unsafe.imports_passed_through():
    pass

WORK_DIR = "/home/ubuntu/.spaghettihub/"


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
                execution_timeout=timedelta(days=1)
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
            start_to_close_timeout=timedelta(seconds=60),
            heartbeat_timeout=timedelta(seconds=30)
        )

        await workflow.wait_condition(lambda: self._completed)

        await workflow.execute_activity(
            "destroy-runner",
            params.id,
            start_to_close_timeout=timedelta(seconds=60),
            heartbeat_timeout=timedelta(seconds=30)
        )
