from datetime import datetime

from pydantic import BaseModel


class MergeProposal(BaseModel):
    id: int
    commit_message: str | None
    date_merged: datetime
    source_git_path: str
    target_git_path: str
    registrant_name: str
    web_link: str
