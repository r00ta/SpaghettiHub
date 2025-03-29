from enum import StrEnum
from typing import Optional

from pydantic import BaseModel


class WorkflowJob(BaseModel):
    run_id: int
    run_url: str
    labels: list[str]
    runner_name: Optional[str]


class WorkflowAction(StrEnum):
    completed = "completed"
    in_progress = "in_progress"
    queued = "queued"
    waiting = "waiting"


class GithubWebhook(BaseModel):
    action: WorkflowAction
    workflow_job: WorkflowJob
