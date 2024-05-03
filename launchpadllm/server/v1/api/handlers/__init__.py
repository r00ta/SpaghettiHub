from launchpadllm.server.base.api.base import API
from launchpadllm.server.v1.api.handlers.merge_proposals import \
    MergeProposalsHandler
from launchpadllm.server.v1.api.handlers.root import RootHandler

APIv1 = API(
    prefix="/api/v1",
    handlers=[
        RootHandler(),
        MergeProposalsHandler()
    ],
)
