from datetime import datetime

from pydantic import BaseModel


class MirroredComment(BaseModel):
    id: int
    fingerprint: str
    github_comment_id: str
    github_source: str
    mp_identifier: str
    created_at: datetime
    posted_at: datetime | None = None
    status: str
    error_message: str | None = None
