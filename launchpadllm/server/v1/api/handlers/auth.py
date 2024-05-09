from pathlib import Path

from fastapi import Depends, Form, HTTPException
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from launchpadllm.common.services.collection import ServiceCollection
from launchpadllm.server.base.api.base import Handler, handler
from launchpadllm.server.v1.api import services

templates_path = Path(__file__).resolve().parent.parent / 'templates'
templates = Jinja2Templates(directory=str(templates_path))


class AuthHandler(Handler):
    """Handler for launchpad to GitHub work."""

    TAGS = ["Auth"]

    @handler(
        path="/login",
        methods=["GET"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=200,
    )
    async def get_login(self,
                        request: Request
                        ):
        """
        Serve the search page.
        """
        return templates.TemplateResponse(
            "login.html", {"request": request}
        )

    @handler(
        path="/login",
        methods=["POST"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=303,
    )
    async def login(self,
                    request: Request,
                    services: ServiceCollection = Depends(services),
                    username: str = Form(),
                    password: str = Form(),
                    ):
        """
        Serve the search page.
        """
        user = await services.users_service.login(username, password)
        if user:
            request.session.update({"username": user.username})
            return RedirectResponse("/v1", status_code=status.HTTP_303_SEE_OTHER)

        return templates.TemplateResponse(
            "login.html", {"request": request, "failed_login": True}
        )

    @handler(
        path="/logout",
        methods=["GET"],
        tags=TAGS,
        response_model_exclude_none=True,
        status_code=303,
    )
    async def logout(self,
                     request: Request,
                     ):
        """
        Serve the search page.
        """
        request.session.clear()
        return RedirectResponse("/v1", status_code=status.HTTP_303_SEE_OTHER)
