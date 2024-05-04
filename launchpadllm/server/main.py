import logging

import uvicorn
from fastapi import FastAPI

from launchpadllm.server.base.api.handlers import APIBase
from launchpadllm.server.base.db.database import Database
from launchpadllm.server.base.middlewares.db import TransactionMiddleware
from launchpadllm.server.settings import Config, read_config
from launchpadllm.server.v1.api.handlers import APIv1


def create_app(config: Config) -> FastAPI:
    """Create the FastAPI application."""

    db = Database(config.db, echo=config.debug_queries)

    app = FastAPI(
        title="Self Service Launchpad",
        name="selfservicelaunchpad",
        # The SwaggerUI page is provided by the APICommon router.
        docs_url=None,
    )

    # The order here is important: the exception middleware must be the first one being executed (i.e. it must be the last
    # middleware added here)
    app.add_middleware(TransactionMiddleware, db=db)

    APIBase.register(app.router)
    APIv1.register(app.router)
    return app


def run():
    app_config = read_config()
    logging.basicConfig(
        level=logging.INFO
    )
    server_config = uvicorn.Config(
        create_app(config=app_config),
        loop="asyncio",
        proxy_headers=True,
        host="0.0.0.0",
        port=1337
    )
    server = uvicorn.Server(server_config)
    server.run()
