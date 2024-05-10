
from spaghettihub.common.db.base import ConnectionProvider


class Service:
    """Base class for services."""

    def __init__(self, session_provider: ConnectionProvider):
        self.session_provider = session_provider
