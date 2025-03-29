from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.services.collection import ServiceCollection
from spaghettihub.common.services.embeddings import EmbeddingsCache


class ServicesV1Middleware(BaseHTTPMiddleware):
    """Run a request in a transaction, handling commit/rollback.

    This makes the database connection available as `request.state.conn`.
    """

    def __init__(self, app: ASGIApp, embeddings_cache: EmbeddingsCache, webhook_secret: str):
        super().__init__(app)
        self.embeddings_cache = embeddings_cache
        self.webhook_secret = webhook_secret

    async def dispatch(
            self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        connection_provider = ConnectionProvider(
            current_connection=request.state.conn)
        request.state.services = ServiceCollection.produce(
            connection_provider, embeddings_cache=self.embeddings_cache, webhook_secret=self.webhook_secret)
        response = await call_next(request)
        return response
