from pydantic import BaseModel


class MyText(BaseModel):
    id: int
    content: str
