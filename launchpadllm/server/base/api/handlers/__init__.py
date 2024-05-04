from launchpadllm.server.base.api.base import API
from launchpadllm.server.base.api.handlers.root import RootHandler

APIBase = API(
    prefix="",
    handlers=[
        RootHandler(),
    ],
)
