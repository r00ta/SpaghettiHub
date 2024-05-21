from pydantic import BaseModel

from spaghettihub.common.models.base import OneToOne
from spaghettihub.common.models.texts import MyText


class Embedding(BaseModel):
    id: int
    embedding: bytes
    text: OneToOne[MyText]
