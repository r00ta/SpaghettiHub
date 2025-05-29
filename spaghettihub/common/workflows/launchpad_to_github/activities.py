import logging
import os
import subprocess
import tempfile
from pathlib import Path

import aiohttp
from temporalio import activity

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.services.collection import ServiceCollection
from spaghettihub.common.workflows.base import ActivityBase
from spaghettihub.common.workflows.launchpad_to_github.params import (
    ActivityCreateGithubBranchForPullRequestParams,
    ActivityCreateGithubPullRequestParams, ActivityUpdateRequestParams, MergeProposalDetails)
from spaghettihub.server.base.db.database import Database

CACHEDIR = "./cache"

logger = logging.getLogger()

class LaunchpadToGithubActivity(ActivityBase):

    def __init__(self, db: Database, gh_token: str):
        super().__init__(db)
        self.gh_token = gh_token

    @activity.defn(name="retrieve-merge-proposal-from-launchpad")
    async def retrieve_merge_proposal_diff_from_launchpad(self, merge_proposal_link: str) -> MergeProposalDetails:
        api_link = merge_proposal_link.replace(
            "https://code.launchpad.net/", "https://api.launchpad.net/devel/")
        async with aiohttp.ClientSession() as session:
            async with session.get(api_link) as response:
                if not 200 <= int(response.status) < 300:
                    raise RuntimeError(f"Status: {response.status}")
                merge_proposal_details = await response.json()
                preview_diff_link = merge_proposal_details["preview_diff_link"]
                preview_diff_link = preview_diff_link + "/+files/preview.diff"
            activity.heartbeat()

            async with session.get(preview_diff_link) as response:
                if not 200 <= int(response.status) < 300:
                    raise RuntimeError(f"Status: {response.status}")
                diff = await response.text()

            async with session.get(merge_proposal_details["source_git_repository_link"]) as response:
                if not 200 <= int(response.status) < 300:
                    raise RuntimeError(f"Status: {response.status}")
                git_repo_details = await response.json()

            return MergeProposalDetails(
                registrant=merge_proposal_details["registrant_link"].split("/")[-1][1:],  # remove the ~
                commit_message=merge_proposal_details["commit_message"],
                description=merge_proposal_details["description"],
                branch=merge_proposal_details["source_git_path"].split("/")[-1],
                repo_url=git_repo_details["git_https_url"],
                diff=diff
            )

    @activity.defn(name="update-github-fork-master-branch")
    async def update_github_fork_master_branch(self, target_dir: str) -> None:
        if not os.path.exists("/tmp/maas-mirror-fork"):
            command = ("git clone git@github.com:r00tabot/maas.git /tmp/maas-mirror-fork && "
                       "cd /tmp/maas-mirror-fork && "
                       "git remote add mirror git@github.com:SpaghettiHub/maas.git && "
                       "git remote update"
                       )
            subprocess.run(command, shell=True, check=True)
            activity.heartbeat()

        update_command = ("cd /tmp/maas-mirror-fork && "
                          "git fetch mirror && "
                          "git fetch origin && "
                          "git reset --hard mirror/master && "
                          "git push origin master -f"
                          )
        subprocess.run(command, shell=True, check=True)

    @activity.defn(name="create-github-branch-for-pull-request")
    async def create_github_branch_for_pull_request(self, params: ActivityCreateGithubBranchForPullRequestParams) -> None:
        command = f"mkdir {params.target_dir} && cp -r /tmp/maas-mirror-fork {params.target_dir}"
        subprocess.run(command, shell=True, check=True)

        activity.heartbeat()

        command = (f"cd {params.target_dir}maas-mirror-fork && "
                   f"git remote add {params.registrant} {params.repo_url} && "
                   f"git fetch {params.registrant} {params.branch} && "
                   f"git checkout master && git branch {params.request_uuid} && git checkout {params.request_uuid} && "
                   f"git merge {params.registrant}/{params.branch}")
        try:
            subprocess.run(command, shell=True, check=True)
        except:
            logger.info("There are conflicts. Trying with diff.")
            # conflict. We use the diff.
            with tempfile.TemporaryDirectory() as tmpdirname:
                temp_dir = Path(tmpdirname)
                diff_file = temp_dir / "patch.diff"
                diff_file.write_text(params.diff)
                command = (f"cd {params.target_dir}maas-mirror-fork && "
                           f"git checkout master && "
                           f"git branch -D {params.request_uuid} && "
                           f"git branch {params.request_uuid} && "
                           f"git checkout {params.request_uuid} && "
                           f"git apply {str(diff_file)} && "
                           f"git add * && git commit -m 'enjoy this from r00ta'")
                subprocess.run(command, shell=True, check=True)

        command = f"git push origin {params.request_uuid}"
        subprocess.run(command, shell=True, check=True)

    @activity.defn(name="create-github-pull-request")
    async def create_github_pull_request(self, params: ActivityCreateGithubPullRequestParams) -> str:
        async with aiohttp.ClientSession() as session:
            json_body = {
                "title": f"Launchpad MP ({params.merge_proposal_id}) - {params.registrant}/{params.branch}",
                "body": f"This is autogenerated by maas.r00ta.com. Enjoy!\n\n\nCommit message: {params.commit_message}",
                "head": f"r00tabot:{params.request_uuid}",
                "base": "master"
            }
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.gh_token}",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            async with session.post("https://api.github.com/repos/SpaghettiHub/maas/pulls",
                                    json=json_body,
                                    headers=headers
                                    ) as response:
                if not 200 <= int(response.status) < 300:
                    raise RuntimeError(f"Status: {response.status}")
                pull_request_response = await response.json()
                return pull_request_response["html_url"]

    @activity.defn(name="complete-request")
    async def complete_request(self, params: ActivityUpdateRequestParams) -> None:
        async with self.start_transaction() as connection:
            connection_provider = ConnectionProvider(
                current_connection=connection)
            services = ServiceCollection.produce(
                connection_provider=connection_provider)
            await services.launchpad_to_github_work_service.finish(request_uuid=params.request_uuid,
                                                                   github_url=params.github_url, status=params.status)
