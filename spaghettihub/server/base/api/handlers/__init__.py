from spaghettihub.server.base.api.base import API
from spaghettihub.server.base.api.handlers.root import RootHandler

APIBase = API(
    prefix="",
    handlers=[
        RootHandler(),
    ],
)
