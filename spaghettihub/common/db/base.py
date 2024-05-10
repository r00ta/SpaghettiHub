from dataclasses import dataclass

from sqlalchemy.engine import Connection


@dataclass
class ConnectionProvider:
    current_connection: Connection | None

    def get_current_connection(self) -> Connection:
        return self.current_connection
