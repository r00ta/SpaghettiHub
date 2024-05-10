import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, List

from temporalio import workflow
from temporalio.common import RetryPolicy

from spaghettihub.common.workflows.constants import TASK_QUEUE_NAME
from spaghettihub.common.workflows.launchpad_to_github.params import \
    TemporalLaunchpadToGithubParams

with workflow.unsafe.imports_passed_through():
    from spaghettihub.common.workflows.launchpad_to_github.activities import (
        ActivityCreateGithubBranchForPullRequestParams,
        ActivityCreateGithubPullRequestParams, ActivityUpdateRequestParams)

WORK_DIR = "/home/ubuntu/.spaghettihub/"


@workflow.defn(name="launchpad-to-github-workflow", sandboxed=False)
class TemporalLaunchpadToGithubWorkflow:

    @workflow.run
    async def run(self, params: TemporalLaunchpadToGithubParams) -> None:
        try:
            return await workflow.execute_child_workflow(
                "internal-launchpad-to-github-workflow",
                params,
                id="internal-launchpad-to-github-workflow" + params.request_uuid,
                task_queue=TASK_QUEUE_NAME,
                retry_policy=RetryPolicy(maximum_attempts=1),
                execution_timeout=timedelta(seconds=120)
            )
        except Exception:
            return await workflow.execute_activity(
                "complete-request",
                ActivityUpdateRequestParams(
                    request_uuid=params.request_uuid,
                    status="FAILED",
                    github_url=None
                ),
                start_to_close_timeout=timedelta(seconds=60),
                heartbeat_timeout=timedelta(seconds=60)
            )


@workflow.defn(name="internal-launchpad-to-github-workflow", sandboxed=False)
class TemporalInternalLaunchpadToGithubWorkflow:

    @workflow.run
    async def run(self, params: TemporalLaunchpadToGithubParams) -> List[TemporalLaunchpadToGithubParams]:
        if not os.path.exists(WORK_DIR):
            os.makedirs(WORK_DIR)

        diff = await workflow.execute_activity(
            "retrieve-merge-proposal-diff-from-launchpad",
            params.merge_proposal_link,
            start_to_close_timeout=timedelta(seconds=60),
            heartbeat_timeout=timedelta(seconds=60)
        )

        request_dir = WORK_DIR + params.request_uuid + "/"
        await workflow.execute_activity(
            "update-github-master-branch",
            request_dir,
            start_to_close_timeout=timedelta(seconds=60),
            heartbeat_timeout=timedelta(seconds=60)
        )

        await workflow.execute_activity(
            "create-github-branch-for-pull-request",
            ActivityCreateGithubBranchForPullRequestParams(
                request_uuid=params.request_uuid,
                target_dir=request_dir,
                diff=diff
            ),
            start_to_close_timeout=timedelta(seconds=60),
            heartbeat_timeout=timedelta(seconds=60)
        )

        github_url = await workflow.execute_activity(
            "create-github-pull-request",
            ActivityCreateGithubPullRequestParams(
                merge_proposal_id=params.merge_proposal_link.split("/")[-1],
                request_uuid=params.request_uuid
            ),
            start_to_close_timeout=timedelta(seconds=60),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=10),
                maximum_interval=timedelta(seconds=60),
            ),
        )

        return await workflow.execute_activity(
            "complete-request",
            ActivityUpdateRequestParams(
                request_uuid=params.request_uuid,
                github_url=github_url,
                status="COMPLETED"
            ),
            start_to_close_timeout=timedelta(seconds=60),
            heartbeat_timeout=timedelta(seconds=60)
        )
