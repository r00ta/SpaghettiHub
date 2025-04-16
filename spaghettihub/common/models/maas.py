from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class WorkflowConclusion(str, Enum):
    success = "success"
    failure = "failure"
    skipped = "skipped"
    cancelled = "cancelled"
    action_required = "action_required"
    neutral = "neutral"
    timed_out = "timed_out"


class MAAS(BaseModel):
    id: int
    commit_sha: str
    commit_message: str | None
    committer_username: str | None
    commit_date: str | None
    continuous_delivery_test_deb_status: WorkflowConclusion | None = None
    continuous_delivery_test_snap_status: WorkflowConclusion | None = None
