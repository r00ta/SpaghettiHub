from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from launchpadllm.common.models.texts import MyText


class Bug(BaseModel):
    id: int
    date_created: datetime
    date_last_updated: datetime
    web_link: str
    title_id: int
    title: MyText | None = None
    description_id: int
    description: MyText | None = None


class BugComment(BaseModel):
    id: int
    text_id: int
    text: MyText | None = None
    bug_id: int


class BugCommentWithScore(BaseModel):
    bug_comment: BugComment
    score: float


class BugWithCommentsAndScores(BaseModel):
    bug: Bug
    title_score: float
    description_score: float
    comments: List[BugCommentWithScore]
