from typing import Any, Dict, Generic, Optional, Sequence, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel


class BaseResponse(BaseModel):
    kind: str


T = TypeVar("T", bound=BaseResponse)


class PaginatedResponse(GenericModel, Generic[T]):
    """
    Base class for paginated responses.
    Derived classes should overwrite the items property
    """

    total: int
    items: Sequence[T]
