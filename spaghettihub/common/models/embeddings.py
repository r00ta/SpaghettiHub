from pydantic import BaseModel


class Embedding(BaseModel):
    id: int
    embedding: bytes
    text_id: int
