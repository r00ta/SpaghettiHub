from fastapi import Query
from pydantic import BaseModel, Field


class MergeProposalMessageMatch(BaseModel):
    query: str = Field(Query())
