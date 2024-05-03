from fastapi import Depends, Request

from launchpadllm.common.services.collection import ServiceCollection


def services(
    request: Request
) -> ServiceCollection:
    """Dependency to return the services collection."""
    return request.state.services
