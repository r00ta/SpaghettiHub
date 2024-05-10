from fastapi import Query
from pydantic import BaseModel, Field


class BugsSearchParam(BaseModel):
    query: str = Field(Query())
