from datetime import datetime
from typing import List

from pydantic import BaseModel

from spaghettihub.common.models.base import OneToMany, OneToOne
from spaghettihub.common.models.texts import MyText


class Bug(BaseModel):
    id: int
    date_created: datetime
    date_last_updated: datetime
    web_link: str
    title: OneToOne[MyText]
    description: OneToOne[MyText]
    comments: OneToMany["BugComment"] | None = None


class BugComment(BaseModel):
    id: int
    text: OneToOne[MyText]
    bug: OneToOne[Bug]


class BugCommentWithScore(BaseModel):
    bug_comment: BugComment
    score: float


class BugWithCommentsAndScores(BaseModel):
    bug: Bug
    title_score: float
    description_score: float
    comments: List[BugCommentWithScore]
