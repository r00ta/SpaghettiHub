from datetime import datetime

from pydantic import BaseModel


class LastUpdate(BaseModel):
    id: int
    last_updated: datetime
