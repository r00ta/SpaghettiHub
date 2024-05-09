from dataclasses import dataclass


@dataclass
class TemporalLaunchpadToGithubParams:
    merge_proposal_link: str
    request_uuid: str


@dataclass
class ActivityCreateGithubPullRequestParams:
    merge_proposal_id: str
    request_uuid: str


@dataclass
class ActivityCreateGithubBranchForPullRequestParams:
    request_uuid: str
    target_dir: str
    diff: str


@dataclass
class ActivityUpdateRequestParams:
    request_uuid: str
    status: str
    github_url: str | None = None
