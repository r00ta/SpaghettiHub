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


class TransactionMiddleware(BaseHTTPMiddleware):
    """Run a request in a transaction, handling commit/rollback.

    This makes the database connection available as `request.state.conn`.
    """

    def __init__(self, app: ASGIApp, db: Database):
        super().__init__(app)
        self.db = db

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[AsyncConnection]:
        """Return the connection in a transaction context manager."""
        async with self.db.engine.connect() as conn:
            async with conn.begin():
                yield conn

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        async with self.get_connection() as conn:
            connection_provider = ConnectionProvider(current_connection=conn)
            request.state.services = ServiceCollection.produce(
                connection_provider)
            response = await call_next(request)
        return response
