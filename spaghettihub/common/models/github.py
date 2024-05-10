from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from spaghettihub.common.models.texts import MyText


class LaunchpadToGithubWork(BaseModel):
    id: int
    requested_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    request_uuid: str
    status: str
    github_url: str | None = None
    launchpad_url: str
