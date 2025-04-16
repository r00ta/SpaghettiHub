from pathlib import Path

from fastapi import Depends, Request
from starlette.templating import Jinja2Templates

from spaghettihub.common.models.runner import GithubWebhook, GithubPushWebhook
from spaghettihub.common.services.collection import ServiceCollection
from spaghettihub.server.base.api.base import Handler, handler
from spaghettihub.server.v1.api import services
from spaghettihub.server.v1.api.models.requests.base import PaginationParams, QuerySearchParam

templates_path = Path(__file__).resolve().parent.parent / 'templates'
templates = Jinja2Templates(directory=str(templates_path))


class GithubWorkflowRunnerHandler(Handler):
    """Handler for github workflow runner work."""

    TAGS = ["Github Workflow Runner"]

    @handler(
        path="/github_workflow_webhook",
        methods=["POST"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=202,
    )
    async def process_webhook(
            self,
            request: Request,
            typed_request: GithubWebhook,
            services: ServiceCollection = Depends(services)
    ):
        services.github_workflow_runner_service.verify_signature(await request.body(), request.headers.get("x-hub-signature-256"))
        await services.github_workflow_runner_service.queue_workflow_webhook(typed_request)

    @handler(
        path="/push_webhook",
        methods=["POST"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=202,
    )
    async def process_push_webhook(
            self,
            request: Request,
            typed_request: GithubPushWebhook,
            services: ServiceCollection = Depends(services)
    ):
        services.github_workflow_runner_service.verify_signature(await request.body(), request.headers.get("x-hub-signature-256"))
        await services.github_workflow_runner_service.queue_push_webhook(typed_request)

    @handler(
        path="/commits",
        methods=["GET"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=200,
    )
    async def get_commits(self, request: Request, services: ServiceCollection = Depends(services)):
        """
        Serve the search page.
        """
        commits = await services.github_workflow_runner_service.list_commits(
            None,
            1,
            10
        )
        return templates.TemplateResponse(
            "commits.html", {"request": request,
                                     "user": request.session.get("username", None),
                                     "results": commits.items,
                                     "query": "",
                                     "size": 10}
        )

    @handler(
        path="/commits:search",
        methods=["GET"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=200,
    )
    async def get_commits_search(self,
                          request: Request,
                          services: ServiceCollection = Depends(services),
                          pagination_params: PaginationParams = Depends(),
                          search: QuerySearchParam = Depends(),
):
        """
        Serve the commits search page
        """
        commits = await services.github_workflow_runner_service.list_commits(
            search.query,
            pagination_params.page,
            pagination_params.size
        )
        return templates.TemplateResponse(
            "commits.html", {"request": request,
                                     "user": request.session.get("username", None),
                                     "results": commits.items,
                                     "query": search.query,
                                     "size": pagination_params.size}
        )