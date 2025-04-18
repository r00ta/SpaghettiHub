from pathlib import Path

from fastapi import Depends, Request
from starlette.templating import Jinja2Templates

from spaghettihub.common.services.collection import ServiceCollection
from spaghettihub.server.base.api.base import Handler, handler
from spaghettihub.server.v1.api import services
from spaghettihub.server.v1.api.models.requests.base import PaginationParams, QuerySearchParam
from spaghettihub.server.v1.api.models.responses.merge_proposals import (
    MergeProposalResponse, MergeProposalsListResponse)

templates_path = Path(__file__).resolve().parent.parent / 'templates'
templates = Jinja2Templates(directory=str(templates_path))


class MergeProposalsHandler(Handler):
    """Handler for merge proposals."""

    TAGS = ["Merge Proposals"]

    @handler(
        path="/merge_proposals",
        methods=["GET"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=200,
    )
    async def get_merge_proposal_template(self, request: Request):
        """
        Serve the search page.
        """
        return templates.TemplateResponse(
            "merge_proposals.html", {
                "request": request, "user": request.session.get("username", None), "size": 5,
                "query": ""}
        )

    @handler(
        path="/merge_proposals:search",
        methods=["GET"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=200,
    )
    async def get_merge_proposal_template_search(
            self,
            request: Request,
            services: ServiceCollection = Depends(services),
            pagination_params: PaginationParams = Depends(),
            message_query_param: QuerySearchParam = Depends(),
    ):
        merge_proposals = await services.merge_proposals_service.find_merge_proposals_contain_message(
            message_query_param.query,
            pagination_params.page,
            pagination_params.size
        )
        return templates.TemplateResponse(
            "merge_proposals.html", {"request": request,
                                     "user": request.session.get("username", None),
                                     "results": merge_proposals.items,
                                     "query": message_query_param.query,
                                     "size": pagination_params.size}
        )

    @handler(
        path="/merge_proposals-stash:search",
        methods=["GET"],
        tags=TAGS,
        responses={
            200: {
                "model": MergeProposalsListResponse,
            }
        },
        response_model_exclude_none=True,
        status_code=200,
    )
    async def find_by_commit_message_match(
            self,
            services: ServiceCollection = Depends(services),
            pagination_params: PaginationParams = Depends(),
            message_query_param: QuerySearchParam = Depends(),
    ) -> MergeProposalsListResponse:
        merge_proposals = await services.merge_proposals_service.find_merge_proposals_contain_message(
            message_query_param.message,
            pagination_params.page,
            pagination_params.size
        )
        return MergeProposalsListResponse(
            items=[
                MergeProposalResponse.from_model(entity=merge_proposal)
                for merge_proposal in merge_proposals.items
            ],
            total=merge_proposals.total,
        )
