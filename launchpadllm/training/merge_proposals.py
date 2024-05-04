import argparse
import asyncio
import datetime
from typing import Optional

from launchpadlib.launchpad import Launchpad
from sqlalchemy.ext.asyncio import create_async_engine
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

from launchpadllm.common.db.base import ConnectionProvider
from launchpadllm.common.db.tables import METADATA
from launchpadllm.common.models.merge_proposals import MergeProposal
from launchpadllm.common.services.collection import ServiceCollection

CACHEDIR = "./cache"


async def get_latest_merge_proposal(connection_provider: ConnectionProvider, services, engine) -> Optional[MergeProposal]:
    async with engine.connect() as conn:
        async with conn.begin():
            connection_provider.current_connection = conn
            merge_proposals = await services.merge_proposals_service.find_merge_proposals_contain_message("", 1, 1)
            return merge_proposals.items[0] if merge_proposals.items else None


async def update_database(engine):
    connection_provider = ConnectionProvider(current_connection=None)
    services = ServiceCollection.produce(connection_provider)
    lp = Launchpad.login_anonymously(
        "Merge proposals crawler", "production", CACHEDIR, version="devel"
    )
    maas = lp.git_repositories.getByPath(path="maas")
    latest_merge_proposal = await get_latest_merge_proposal(connection_provider, services, engine)
    for merge_proposal in tqdm(maas.getMergeProposals(status="Merged"), desc=f"Processing merge proposals"):
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


async def async_main():
    parser = argparse.ArgumentParser(
        description="Launchpad Merge Proposal populator",
    )
    parser.add_argument(
        "-p", "--project", default="maas", help="Launchpad project name"
    )
    parser.add_argument(
        "-d", "--dsn", default="postgresql+asyncpg://launchpadllm:launchpadllm@localhost:5432/launchpadllm",
        help="The database DSN"
    )
    args = parser.parse_args()

    engine = create_async_engine(args.dsn)
    async with engine.begin() as conn:
        await conn.run_sync(METADATA.create_all)

    await update_database(args, engine)
    await engine.dispose()


def main():
    asyncio.run(async_main())
