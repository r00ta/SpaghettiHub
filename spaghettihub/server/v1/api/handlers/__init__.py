from spaghettihub.server.base.api.base import API
from spaghettihub.server.v1.api.handlers.auth import AuthHandler
from spaghettihub.server.v1.api.handlers.bugs import BugsHandler
from spaghettihub.server.v1.api.handlers.github import \
    LaunchpadToGithubWorkHandler
from spaghettihub.server.v1.api.handlers.merge_proposals import \
    MergeProposalsHandler
from spaghettihub.server.v1.api.handlers.root import RootHandler

APIv1 = API(
    prefix="/v1",
    handlers=[
        RootHandler(),
        MergeProposalsHandler(),
        LaunchpadToGithubWorkHandler(),
        BugsHandler(),
        AuthHandler()
    ],
)
