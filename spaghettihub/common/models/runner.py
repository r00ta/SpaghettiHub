from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from spaghettihub.common.models.maas import WorkflowConclusion


class WorkflowJob(BaseModel):
    id: int
    name: str
    workflow_name: str
    head_branch: str
    head_sha: str
    conclusion: Optional[WorkflowConclusion]
    run_url: str
    labels: list[str]
    runner_name: Optional[str]


class WorkflowAction(str, Enum):
    completed = "completed"
    in_progress = "in_progress"
    queued = "queued"
    waiting = "waiting"


class GithubWebhook(BaseModel):
    action: WorkflowAction
    workflow_job: WorkflowJob


class CommitAuthor(BaseModel):
    name: str
    email: str
    username: str


class GithubCommit(BaseModel):
    id: str
    author: CommitAuthor
    message: str
    timestamp: datetime


class GithubPushWebhook(BaseModel):
    """ we always push one commit after another, so we can ignore the 'commits' """
    ref: str
    commits: list[GithubCommit]
    head_commit: GithubCommit
