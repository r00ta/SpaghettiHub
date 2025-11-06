from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MirroredComment(BaseModel):
    id: int
    fingerprint: str
    github_comment_id: str
    github_source: str
    mp_identifier: str
    created_at: datetime
    posted_at: Optional[datetime] = None
    status: str
    error_message: Optional[str] = None
