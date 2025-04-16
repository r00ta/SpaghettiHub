from temporalio.client import Client

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.db.bugs import BugsRepository
from spaghettihub.common.db.embeddings import EmbeddingsRepository
from spaghettihub.common.db.github import LaunchpadToGithubWorkRepository
from spaghettihub.common.db.last_update import LastUpdateRepository
from spaghettihub.common.db.maas import MAASRepository
from spaghettihub.common.db.merge_proposals import MergeProposalsRepository
from spaghettihub.common.db.texts import TextsRepository
from spaghettihub.common.db.users import UsersRepository
from spaghettihub.common.services.bugs import BugsService
from spaghettihub.common.services.embeddings import (EmbeddingsCache,
                                                     EmbeddingsService)
from spaghettihub.common.services.github import LaunchpadToGithubWorkService
from spaghettihub.common.services.last_update import LastUpdateService
from spaghettihub.common.services.merge_proposals import MergeProposalsService
from spaghettihub.common.services.runner import GithubWorkflowRunnerService
from spaghettihub.common.services.texts import TextsService
from spaghettihub.common.services.users import UsersService


class ServiceCollection:
    last_update_service: LastUpdateService
    bugs_service: BugsService
    texts_service: TextsService
    embeddings_service: EmbeddingsService
    merge_proposals_service: MergeProposalsService
    launchpad_to_github_work_service: LaunchpadToGithubWorkService
    users_service: UsersService
    github_workflow_runner_service: GithubWorkflowRunnerService

    @classmethod
    def produce(cls, connection_provider: ConnectionProvider, embeddings_cache: EmbeddingsCache | None = None,
                webhook_secret: str | None = None, temporal_client: Client | None = None) -> "ServiceCollection":
        services = cls()
        services.last_update_service = LastUpdateService(
            connection_provider=connection_provider,
            last_update_repository=LastUpdateRepository(
                connection_provider=connection_provider
            ),
        )
        services.texts_service = TextsService(
            connection_provider=connection_provider,
            texts_repository=TextsRepository(
                connection_provider=connection_provider),
        )
        services.bugs_service = BugsService(
            connection_provider=connection_provider,
            bugs_repository=BugsRepository(
                connection_provider=connection_provider),
            texts_service=services.texts_service,
        )
        services.embeddings_service = EmbeddingsService(
            connection_provider=connection_provider,
            embeddings_repository=EmbeddingsRepository(
                connection_provider=connection_provider
            ),
            texts_service=services.texts_service,
            bugs_service=services.bugs_service,
            embeddings_cache=embeddings_cache
        )
        services.merge_proposals_service = MergeProposalsService(
            connection_provider=connection_provider,
            merge_proposals_repository=MergeProposalsRepository(
                connection_provider=connection_provider
            )
        )
        services.launchpad_to_github_work_service = LaunchpadToGithubWorkService(
            connection_provider=connection_provider,
            launchpad_to_github_work_repository=LaunchpadToGithubWorkRepository(
                connection_provider=connection_provider
            ),
            temporal_client=temporal_client
        )
        services.github_workflow_runner_service = GithubWorkflowRunnerService(
            connection_provider=connection_provider,
            maas_repository=MAASRepository(connection_provider=connection_provider),
            webhook_secret=webhook_secret,
            temporal_client=temporal_client
        )
        services.users_service = UsersService(
            connection_provider=connection_provider,
            users_repository=UsersRepository(
                connection_provider=connection_provider
            )
        )
        return services
