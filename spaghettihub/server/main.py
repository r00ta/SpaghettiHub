import argparse
import logging

import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from transformers import AutoModel, AutoTokenizer

from spaghettihub.common.services.embeddings import EmbeddingsCache
from spaghettihub.server.base.api.handlers import APIBase
from spaghettihub.server.base.db.database import Database
from spaghettihub.server.base.middlewares.db import TransactionMiddleware
from spaghettihub.server.settings import Config, read_config
from spaghettihub.server.v1.api.handlers import APIv1
from spaghettihub.server.v1.middlewares.services import ServicesV1Middleware


def nullable_str(val: str):
    if not val or val == "None":
        return None
    return val


def make_arg_parser():
    parser = argparse.ArgumentParser(
        description="LauchpadLLM server.")
    parser.add_argument("--host",
                        type=str,
                        default="0.0.0.0",
                        help="host name")
    parser.add_argument("--port", type=int, default=8000, help="port number")
    parser.add_argument(
        "--uvicorn-log-level",
        type=str,
        default="info",
        choices=['debug', 'info', 'warning', 'error', 'critical', 'trace'],
        help="log level for uvicorn")
    parser.add_argument("--ssl-keyfile",
                        type=nullable_str,
                        default=None,
                        help="The file path to the SSL key file")
    parser.add_argument("--ssl-certfile",
                        type=nullable_str,
                        default=None,
                        help="The file path to the SSL cert file")
    parser.add_argument("--ssl-ca-certs",
                        type=nullable_str,
                        default=None,
                        help="The CA certificates file")
    parser.add_argument("--secret",
                        type=str,
                        required=True,
                        help="Set the session secret")
    parser.add_argument("--webhook-secret",
                        type=str,
                        required=True,
                        help="Set the webhook secret")
    return parser


def create_app(config: Config) -> FastAPI:
    """Create the FastAPI application."""

    db = Database(config.db, echo=config.debug_queries)

    app = FastAPI(
        title="Spaghetti Hub",
        name="My Spaghetti Hub tools",
        # The SwaggerUI page is provided by the APICommon router.
        docs_url=None,
    )

    # The order here is important: the exception middleware must be the first one being executed (i.e. it must be the last
    # middleware added here)
    embeddings_cache = EmbeddingsCache(
        model=AutoModel.from_pretrained("BAAI/bge-large-en-v1.5"),
        tokenizer=AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")
    )
    app.add_middleware(ServicesV1Middleware, embeddings_cache=embeddings_cache, webhook_secret=config.webhook_secret)
    app.add_middleware(TransactionMiddleware, db=db)
    app.add_middleware(
        SessionMiddleware,
        same_site="strict",
        secret_key=config.secret,
    )

    APIBase.register(app.router)
    APIv1.register(app.router)
    return app


def run():
    parser = make_arg_parser()
    args = parser.parse_args()

    app_config = read_config(secret=args.secret, webhook_secret=args.webhook_secret)
    logging.basicConfig(
        level=logging.INFO
    )
    server_config = uvicorn.Config(
        create_app(config=app_config),
        loop="asyncio",
        proxy_headers=True,
        host=args.host,
        port=args.port,
        ssl_keyfile=args.ssl_keyfile,
        ssl_certfile=args.ssl_certfile,
        ssl_ca_certs=args.ssl_ca_certs
    )
    server = uvicorn.Server(server_config)
    server.run()
