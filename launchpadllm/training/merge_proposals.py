import argparse
import asyncio
import datetime

from launchpadlib.launchpad import Launchpad
from sqlalchemy.ext.asyncio import create_async_engine
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

from launchpadllm.common.db.base import ConnectionProvider
from launchpadllm.common.db.tables import METADATA
from launchpadllm.common.services.collection import ServiceCollection

CACHEDIR = "./cache"


async def update_database(args, engine):
    connection_provider = ConnectionProvider(current_connection=None)
    services = ServiceCollection.produce(connection_provider)
    lp = Launchpad.login_anonymously(
        "Merge proposals crawler", "production", CACHEDIR, version="devel"
    )
    maas = lp.git_repositories.getByPath(path="maas")
    for merge_proposal in tqdm(maas.getMergeProposals(status="Merged"), desc=f"Processing merge proposals"):
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
    subparsers = parser.add_subparsers(dest="command", help="commands")
    update_parser = subparsers.add_parser(
        "update", help="Update the database with the latest merge proposals"
    )
    search_parser = subparsers.add_parser(
        "search", help="Search the database for matching merge proposals"
    )
    search_parser.add_argument("query", type=str, help="Search prompt")
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        exit(1)

    engine = create_async_engine(
        "postgresql+asyncpg://launchpadllm:launchpadllm@localhost:5432/launchpadllm"
    )
    async with engine.begin() as conn:
        await conn.run_sync(METADATA.create_all)

    if args.command == "update":
        await update_database(args, engine)
    # elif args.command == "search":
    #     searcher = Search(st)
    #     pprint.pprint(searcher.find_similar_issues(args.query, limit=args.limit))
    # st.close()


def main():
    asyncio.run(async_main())
