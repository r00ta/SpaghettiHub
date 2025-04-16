import argparse
import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from spaghettihub.common.workflows.constants import TASK_QUEUE_NAME
from spaghettihub.common.workflows.launchpad_to_github.activities import \
    LaunchpadToGithubActivity
from spaghettihub.common.workflows.launchpad_to_github.workflow import (
    TemporalInternalLaunchpadToGithubWorkflow,
    TemporalLaunchpadToGithubWorkflow)
from spaghettihub.common.workflows.runner.activities import GithubRunnerActivity
from spaghettihub.common.workflows.runner.workflow import TemporalGithubRunnerWorkflow, TemporalInternalGithubRunnerWorkflow, \
    GithubWorkflowWebhookRunnerWorkflow, GithubPushWebhookWorkflow
from spaghettihub.server.base.db.database import Database
from spaghettihub.server.settings import read_config


async def main(gh_token: str, gh_runner_token: str, lxd_host: str, lxd_trusted_password: str):
    client = await Client.connect("localhost:7233")

    db = Database(config=read_config().db)

    launchpad_to_github_activity = LaunchpadToGithubActivity(db, gh_token)
    github_runner_activity = GithubRunnerActivity(db, gh_runner_token, lxd_host, lxd_trusted_password)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE_NAME,
        workflows=[TemporalLaunchpadToGithubWorkflow,
                   TemporalInternalLaunchpadToGithubWorkflow,
                   TemporalGithubRunnerWorkflow,
                   TemporalInternalGithubRunnerWorkflow,
                   GithubWorkflowWebhookRunnerWorkflow,
                   GithubPushWebhookWorkflow
                   ],
        activities=[
            launchpad_to_github_activity.retrieve_merge_proposal_diff_from_launchpad,
            launchpad_to_github_activity.update_github_master_branch,
            launchpad_to_github_activity.update_github_fork_master_branch,
            launchpad_to_github_activity.create_github_branch_for_pull_request,
            launchpad_to_github_activity.create_github_pull_request,
            launchpad_to_github_activity.complete_request,
            github_runner_activity.get_registration_token,
            github_runner_activity.spawn_runner,
            github_runner_activity.destroy_runner,
            github_runner_activity.update_commit_metadata,
            github_runner_activity.update_continuous_delivery_commit_metadata,
        ],
    )
    await worker.run()


def run():
    parser = argparse.ArgumentParser(
        description="LauchpadLLM worker.")
    parser.add_argument("--gh_token",
                        type=str,
                        help="The github token")
    parser.add_argument("--gh_runner_token",
                        type=str,
                        help="The github runner token")
    parser.add_argument("--lxd_host",
                        type=str,
                        help="The LXD host")
    parser.add_argument("--lxd_trusted_password",
                        type=str,
                        help="The LXD trusted password")
    args = parser.parse_args()
    asyncio.run(main(args.gh_token, args.gh_runner_token, args.lxd_host, args.lxd_trusted_password))
