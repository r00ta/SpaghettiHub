from fastapi import HTTPException, Request
from fastapi.security import APIKeyCookie
from starlette import status

from spaghettihub.common.services.collection import ServiceCollection


def services(
        request: Request
) -> ServiceCollection:
    """Dependency to return the services collection."""
    return request.state.services


security = APIKeyCookie(name="session")


def authenticated(
        request: Request
):
    if username := request.session.get("username", None):
        return username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You are not logged in.",
    )
