from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from spaghettihub.server.base.api.base import Handler, handler

templates_path = Path(__file__).resolve().parent.parent / 'templates'
templates = Jinja2Templates(directory=str(templates_path))


class RootHandler(Handler):
    """Root API handler."""

    @handler(path="/", methods=["GET"], include_in_schema=False)
    async def get(self, request: Request):
        return RedirectResponse("/v1")
