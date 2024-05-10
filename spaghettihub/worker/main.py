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
from spaghettihub.server.base.db.database import Database
from spaghettihub.server.settings import read_config


async def main(gh_token: str):
    client = await Client.connect("localhost:7233")

    db = Database(config=read_config().db)

    launchpad_to_github_activity = LaunchpadToGithubActivity(db, gh_token)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE_NAME,
        workflows=[TemporalLaunchpadToGithubWorkflow,
                   TemporalInternalLaunchpadToGithubWorkflow],
        activities=[
            launchpad_to_github_activity.retrieve_merge_proposal_diff_from_launchpad,
            launchpad_to_github_activity.update_github_master_branch,
            launchpad_to_github_activity.create_github_branch_for_pull_request,
            launchpad_to_github_activity.create_github_pull_request,
            launchpad_to_github_activity.complete_request
        ],
    )
    await worker.run()


def run():
    parser = argparse.ArgumentParser(
        description="LauchpadLLM worker.")
    parser.add_argument("--gh_token",
                        type=str,
                        help="The github token")
    args = parser.parse_args()
    asyncio.run(main(args.gh_token))
