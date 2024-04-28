
from launchpadllm.common.db.base import ConnectionProvider
from launchpadllm.common.db.bugs import BugsRepository
from launchpadllm.common.db.embeddings import EmbeddingsRepository
from launchpadllm.common.db.last_update import LastUpdateRepository
from launchpadllm.common.db.texts import TextsRepository
from launchpadllm.common.services.bugs import BugsService
from launchpadllm.common.services.embeddings import EmbeddingsService
from launchpadllm.common.services.last_update import LastUpdateService
from launchpadllm.common.services.texts import TextsService


class ServiceCollection:
    last_update_service: LastUpdateService
    bugs_service: BugsService
    texts_service: TextsService
    embeddings_service: EmbeddingsService

    @classmethod
    def produce(cls, connection_provider: ConnectionProvider) -> "ServiceCollection":
        services = cls()
        services.last_update_service = LastUpdateService(
            connection_provider=connection_provider,
            last_update_repository=LastUpdateRepository(
                connection_provider=connection_provider
            ),
        )
        services.texts_service = TextsService(
            connection_provider=connection_provider,
            texts_repository=TextsRepository(connection_provider=connection_provider),
        )
        services.bugs_service = BugsService(
            connection_provider=connection_provider,
            bugs_repository=BugsRepository(connection_provider=connection_provider),
            texts_service=services.texts_service,
        )
        services.embeddings_service = EmbeddingsService(
            connection_provider=connection_provider,
            embeddings_repository=EmbeddingsRepository(
                connection_provider=connection_provider
            ),
            texts_service=services.texts_service,
        )
        return services
