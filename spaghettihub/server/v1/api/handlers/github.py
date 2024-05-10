from pathlib import Path

from fastapi import Depends, Form, Request
from starlette.templating import Jinja2Templates

from spaghettihub.common.services.collection import ServiceCollection
from spaghettihub.server.base.api.base import Handler, handler
from spaghettihub.server.v1.api import authenticated, services

templates_path = Path(__file__).resolve().parent.parent / 'templates'
templates = Jinja2Templates(directory=str(templates_path))


class LaunchpadToGithubWorkHandler(Handler):
    """Handler for launchpad to GitHub work."""

    TAGS = ["Launchpad To Github work"]

    @handler(
        path="/launchpad_to_github",
        methods=["GET"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=200,
        dependencies=[Depends(authenticated)]
    )
    async def get_launchpad_to_github_page(self, request: Request):
        """
        Serve the search page.
        """
        return templates.TemplateResponse(
            "launchpad_to_github.html", {"request": request, "user": request.session.get(
                "username", None), "launchpad_url": ""}
        )

    @handler(
        path="/launchpad_to_github",
        methods=["POST"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=202,
        dependencies=[Depends(authenticated)]
    )
    async def create_launchpad_to_github_work(
            self,
            request: Request,
            launchpad_url: str = Form(),
            services: ServiceCollection = Depends(services)
    ):
        work = await services.launchpad_to_github_work_service.create(launchpad_url)
        return templates.TemplateResponse(
            "launchpad_to_github.html",
            {"request": request,
             "work": work,
             "refresh_page": "/v1/launchpad_to_github/" + work.request_uuid,
             "launchpad_url": work.launchpad_url
             }
        )

    @handler(
        path="/launchpad_to_github/{work_id}",
        methods=["GET"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=200,
        dependencies=[Depends(authenticated)]
    )
    async def get_launchpad_to_github_work(
            self,
            request: Request,
            work_id: str,
            services: ServiceCollection = Depends(services)
    ):
        work = await services.launchpad_to_github_work_service.get(work_id)
        return templates.TemplateResponse(
            "launchpad_to_github.html",
            {"request": request,
             "work": work,
             "refresh_page": "/v1/launchpad_to_github/" + work.request_uuid if work.status == "NEW" else None,
             "launchpad_url": work.launchpad_url
             }
        )
