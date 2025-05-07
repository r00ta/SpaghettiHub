from dataclasses import dataclass



@dataclass
class TemporalLaunchpadToGithubParams:
    merge_proposal_link: str
    request_uuid: str

@dataclass
class MergeProposalDetails:
    registrant: str
    commit_message: str
    description: str
    branch: str
    repo_url: str


@dataclass
class ActivityCreateGithubPullRequestParams:
    merge_proposal_id: str
    request_uuid: str
    commit_message: str

@dataclass
class ActivityCreateGithubBranchForPullRequestParams:
    request_uuid: str
    target_dir: str
    merge_proposal_details: MergeProposalDetails


@dataclass
class ActivityUpdateRequestParams:
    request_uuid: str
    status: str
    github_url: str | None = None

