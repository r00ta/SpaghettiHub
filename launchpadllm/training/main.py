import argparse
import asyncio
import datetime
import multiprocessing
import time
from functools import partial

from launchpadlib.launchpad import Launchpad
from sqlalchemy.ext.asyncio import create_async_engine
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

from launchpadllm.common.db.base import ConnectionProvider
from launchpadllm.common.db.tables import METADATA
from launchpadllm.common.services.collection import ServiceCollection
from launchpadllm.training.bugs.embedding_worker import EmbeddingWorker

CACHEDIR = "./cache"
BUG_STATES = [
    "New",
    "Triaged",
    "Confirmed",
    "In Progress",
    "Fix Committed",
    "Fix Released",
    "Incomplete",
    "Invalid",
    "Won't Fix",
]


async def process_embeddings_in_parallel(dsn, texts):
    text_queue = multiprocessing.Queue()
    for text in texts:
        text_queue.put(text)

    num_processes = multiprocessing.cpu_count()
    workers = {i: EmbeddingWorker(dsn, text_queue)
               for i in range(num_processes)}
    for idx, worker in workers.items():
        worker.start()

    with tqdm(total=len(texts), desc="Generating Embeddings") as pbar:
        while text_queue:
            left_texts = text_queue.qsize()
            pbar.update(left_texts)
            await asyncio.sleep(5)


async def update_database(args, dsn, engine):
    connection_provider = ConnectionProvider(current_connection=None)
    services = ServiceCollection.produce(connection_provider)
    lp = Launchpad.login_anonymously(
        "Bug Triage Assistant", "production", CACHEDIR, version="devel"
    )
    project = lp.projects[args.project]
    current_date = datetime.datetime.utcnow()
    async with engine.connect() as conn:
        async with conn.begin():
            connection_provider.current_connection = conn
            last_updated = await services.last_update_service.get_last_update()
    if last_updated:
        tqdm.write(f"Last update: {last_updated.last_updated}")
        new_bugs = project.searchTasks(
            status=BUG_STATES, created_since=last_updated.last_updated
        )

        if len(new_bugs) == 0:
            tqdm.write(f"Processing bugs [NEW]: no changes")
        else:
            for b in tqdm(new_bugs, desc=f"Processing bugs [NEW]"):
                async with engine.connect() as conn:
                    async with conn.begin():
                        connection_provider.current_connection = conn
                        await services.bugs_service.process_launchpad_bug(b)

        modified_bugs = (
            project.searchTasks(
                status=BUG_STATES, modified_since=last_updated.last_updated
            ),
        )
        if len(modified_bugs) == 0:
            tqdm.write(f"Processing bugs [MODIFIED]: no changes")
        else:
            for b in tqdm(new_bugs, desc=f"Processing bugs [MODIFIED]"):
                async with engine.connect() as conn:
                    async with conn.begin():
                        connection_provider.current_connection = conn
                        await services.bugs_service.process_launchpad_bug(b)

    else:
        all_bugs = project.searchTasks(status=BUG_STATES)
        if len(all_bugs) == 0:
            tqdm.write(f"Processing bugs [ALL]: no changes")
        else:
            for b in tqdm(all_bugs, desc=f"Processing bugs [ALL]"):
                async with engine.connect() as conn:
                    async with conn.begin():
                        connection_provider.current_connection = conn
                        await services.bugs_service.process_launchpad_bug(b)

    async with engine.connect() as conn:
        async with conn.begin():
            connection_provider.current_connection = conn
            await services.last_update_service.set_last_update(current_date)
            texts = await services.texts_service.find_texts_without_embeddings()

    await process_embeddings_in_parallel(dsn, texts)


async def async_main():
    parser = argparse.ArgumentParser(
        description="Launchpad Bug Triage Assistant",
    )
    parser.add_argument(
        "-p", "--project", default="maas", help="Launchpad project name"
    )
    subparsers = parser.add_subparsers(dest="command", help="commands")
    update_parser = subparsers.add_parser(
        "update", help="Update the database with the latest issues"
    )
    search_parser = subparsers.add_parser(
        "search", help="Search the database for matching issues"
    )
    search_parser.add_argument("query", type=str, help="Search prompt")
    search_parser.add_argument(
        "--limit", type=int, default=5, help="Maximum number of returned results"
    )
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        exit(1)

    # engine = create_async_engine("sqlite+aiosqlite:///lauchpad_llm.sqlite")

    dsn = "postgresql+asyncpg://launchpadllm:launchpadllm@localhost:5432/launchpadllm"
    engine = create_async_engine(
        dsn
    )
    async with engine.begin() as conn:
        await conn.run_sync(METADATA.create_all)

    if args.command == "update":
        await update_database(args, dsn, engine)
    # elif args.command == "search":
    #     searcher = Search(st)
    #     pprint.pprint(searcher.find_similar_issues(args.query, limit=args.limit))
    # st.close()


def main():
    asyncio.run(async_main())
