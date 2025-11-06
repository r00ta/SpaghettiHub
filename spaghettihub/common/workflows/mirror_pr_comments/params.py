from dataclasses import dataclass
from typing import List


@dataclass
class MirrorPullRequestCommentsParams:
    github_pr_url: str
    launchpad_mp_url: str
    include_outdated: bool = False
    include_review_states: bool = False


@dataclass
class ParsedInputParams:
    github_owner: str
    github_repo: str
    github_pr_number: int
    mp_identifier: str


@dataclass
class UnifiedComment:
    source: str  # "issue" or "review"
    id: str
    author_login: str
    body: str
    created_at: str
    path: str | None = None
    line: int | None = None
    fingerprint: str = ""


@dataclass
class FetchCommentsResult:
    comments: List[UnifiedComment]


@dataclass
class FilterDeduplicateResult:
    new_comments: List[UnifiedComment]
    skipped_count: int


@dataclass
class PostCommentsResult:
    posted_count: int
    error_count: int
    errors: List[str]


@dataclass
class MirrorCommentsResult:
    fetched_count: int
    posted_count: int
    skipped_count: int
    error_count: int
    errors: List[str]
