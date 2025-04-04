from enum import Enum
from typing import Optional

from pydantic import BaseModel


class WorkflowJob(BaseModel):
    id: int
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
