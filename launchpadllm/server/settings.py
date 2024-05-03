from dataclasses import dataclass

from sqlalchemy import URL


@dataclass
class DatabaseConfig:
    name: str
    host: str
    username: str | None = None
    password: str | None = None
    port: int | None = None

    @property
    def dsn(self) -> URL:
        return URL.create(
            "postgresql+asyncpg",
            host=self.host,
            port=self.port,
            database=self.name,
            username=self.username,
            password=self.password,
        )


@dataclass
class Config:
    db: DatabaseConfig | None
    debug_queries: bool = False
    debug: bool = False


def read_config() -> Config:
    return Config(
        # TODO: do not hardcode this
        DatabaseConfig(
            "launchpadllm",
            "localhost",
            "launchpadllm",
            "launchpadllm",
            5432
        ),
        debug_queries=False,
        debug=False)
