import argparse
import asyncio
import datetime
from typing import Optional

from launchpadlib.launchpad import Launchpad
from sqlalchemy.ext.asyncio import create_async_engine
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.db.tables import METADATA
from spaghettihub.common.models.merge_proposals import MergeProposal
from spaghettihub.common.services.collection import ServiceCollection

CACHEDIR = "./cache"


async def get_latest_merge_proposal(connection_provider: ConnectionProvider, services, engine) -> Optional[MergeProposal]:
    async with engine.connect() as conn:
        async with conn.begin():
            connection_provider.current_connection = conn
            # Latest MPs come first
            merge_proposals = await services.merge_proposals_service.find_merge_proposals_contain_message("", 1, 1)
            return merge_proposals.items[0] if merge_proposals.items else None


async def process_merge_proposals(engine, connection_provider, services, latest_merge_proposal, merge_proposals, branch):
    for merge_proposal in tqdm(merge_proposals, desc=f"Processing merge proposals from branch " + branch):
        if latest_merge_proposal and latest_merge_proposal.date_merged > merge_proposal.date_merged:
            # Stop processing the MPs as we already have them
            break
        async with engine.connect() as conn:
            async with conn.begin():
                connection_provider.current_connection = conn
                await services.merge_proposals_service.create(
                    commit_message=merge_proposal.commit_message,
                    date_merged=merge_proposal.date_merged,
                    source_git_path=merge_proposal.source_git_path,
                    target_git_path=merge_proposal.target_git_path,
                    registrant_name=merge_proposal.registrant_link.split("~")[
                        1],
                    web_link=merge_proposal.web_link
                )


async def update_database(engine):
    connection_provider = ConnectionProvider(current_connection=None)
    services = ServiceCollection.produce(connection_provider)
    lp = Launchpad.login_anonymously(
        "Merge proposals crawler", "production", CACHEDIR, version="devel"
    )
    latest_merge_proposal = await get_latest_merge_proposal(connection_provider, services, engine)

    blz_repo_mps = lp.branches.getByPath(
        path="~maas-committers/maas/trunk").getMergeProposals(status="Merged")
    await process_merge_proposals(engine, connection_provider, services, latest_merge_proposal, blz_repo_mps, "blz")

    maas = lp.git_repositories.getByPath(path="maas")
    git_repo_mps = maas.getMergeProposals(status="Merged")
    await process_merge_proposals(engine, connection_provider, services, latest_merge_proposal, git_repo_mps, "blz")


async def async_main():
    parser = argparse.ArgumentParser(
        description="Spaghetti Hub Merge Proposal populator",
    )
    parser.add_argument(
        "-p", "--project", default="maas", help="Launchpad project name"
    )
    parser.add_argument(
        "-d", "--dsn", default="postgresql+asyncpg://spaghettihub:spaghettihub@localhost:5432/spaghettihub",
        help="The database DSN"
    )
    args = parser.parse_args()

    engine = create_async_engine(args.dsn)
    async with engine.begin() as conn:
        await conn.run_sync(METADATA.create_all)

    await update_database(engine)
    await engine.dispose()


def main():
    asyncio.run(async_main())
