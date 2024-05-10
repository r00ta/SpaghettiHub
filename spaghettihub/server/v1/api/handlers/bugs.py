from pathlib import Path

from fastapi import Depends, Request
from starlette.templating import Jinja2Templates

from spaghettihub.common.services.collection import ServiceCollection
from spaghettihub.server.base.api.base import Handler, handler
from spaghettihub.server.v1.api import services
from spaghettihub.server.v1.api.models.requests.base import PaginationParams
from spaghettihub.server.v1.api.models.requests.bugs import BugsSearchParam
from spaghettihub.server.v1.api.models.requests.merge_proposals import \
    MergeProposalMessageMatch
from spaghettihub.server.v1.api.models.responses.merge_proposals import (
    MergeProposalResponse, MergeProposalsListResponse)

templates_path = Path(__file__).resolve().parent.parent / 'templates'
templates = Jinja2Templates(directory=str(templates_path))


class BugsHandler(Handler):
    """Handler for merge proposals."""

    TAGS = ["Bugs"]

    @handler(
        path="/bugs",
        methods=["GET"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=200,
    )
    async def get_bugs(self, request: Request):
        """
        Serve the search page.
        """
        return templates.TemplateResponse(
            "bugs.html", {"request": request,
                          "user": request.session.get("username", None),
                          "size": 5,
                          "query": ""}
        )

    @handler(
        path="/bugs:search",
        methods=["GET"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=200,
    )
    async def get_bugs_search(
        self,
        request: Request,
        services: ServiceCollection = Depends(services),
        pagination_params: PaginationParams = Depends(),
        search: BugsSearchParam = Depends(),
    ):
        bugs = await services.embeddings_service.find_similar_issues(search.query, pagination_params.size)
        return templates.TemplateResponse(
            "bugs.html", {"request": request,
                          "user": request.session.get("username", None),
                          "results": bugs,
                          "query": search.query,
                          "size": pagination_params.size}
        )
