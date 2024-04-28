from datetime import datetime

from pydantic import BaseModel


class Bug(BaseModel):
    id: int
    date_created: datetime
    date_last_updated: datetime
    web_link: str
    title_id: int
    description_id: int


class BugComment(BaseModel):
    id: int
    text_id: int
    bug_id: int
