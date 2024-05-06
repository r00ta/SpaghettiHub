import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Awaitable, Callable

from fastapi import Request, Response
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncConnection
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from launchpadllm.common.db.base import ConnectionProvider
from launchpadllm.common.services.collection import ServiceCollection
from launchpadllm.server.base.db.database import Database
from launchpadllm.server.v1.models.embeddings import EmbeddingsCache


class ServicesV1Middleware(BaseHTTPMiddleware):
    """Run a request in a transaction, handling commit/rollback.

    This makes the database connection available as `request.state.conn`.
    """

    def __init__(self, app: ASGIApp, embeddings_cache: EmbeddingsCache):
        super().__init__(app)
        self.embeddings_cache = embeddings_cache

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        connection_provider = ConnectionProvider(
            current_connection=request.state.conn)
        request.state.services = ServiceCollection.produce(
            connection_provider, embeddings_cache=self.embeddings_cache)
        response = await call_next(request)
        return response
