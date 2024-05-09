from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from launchpadllm.common.models.texts import MyText


class User(BaseModel):
    id: int
    username: str
    password: str
