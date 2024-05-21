from dataclasses import dataclass
from typing import Generic, List, Sequence, TypeVar, Union

from pydantic import BaseModel, Field, PrivateAttr
from pydantic.generics import GenericModel

T = TypeVar("T")


@dataclass
class ListResult(Generic[T]):
    """
    Encapsulates the result of calling a Repository method than returns a list. It includes the items and the number of items
    that matched the query.
    """

    items: Sequence[T]
    total: int


class Unset(BaseModel):
    # Sentinel object
    pass


class OneToOne(GenericModel, Generic[T]):

    _id: Union[int, None] = PrivateAttr(default=None)
    _id_loaded: bool = PrivateAttr(default=False)

    _ref: Union[T, None] = PrivateAttr(default=None)
    _ref_loaded: bool = PrivateAttr(default=False)

    def __init__(self, id: Union[int, None, Unset] = Unset(), ref: Union[T, None, Unset] = Unset(), **data):
        super().__init__(**data)

        id_loaded = not isinstance(id, Unset)
        ref_loaded = not isinstance(ref, Unset)

        self._id_loaded = id_loaded
        self._id = id if id_loaded else None
        self._ref_loaded = ref_loaded
        self._ref = ref if ref_loaded else None

    @property
    def id(self) -> Union[int, None]:
        if not self._id_loaded:
            raise Exception("ID are not loaded")
        return self._id

    def set_id(self, id: int):
        self._id = id
        self._id_loaded = True

    @property
    def ref(self) -> Union[T, None]:
        if not self._ref_loaded:
            raise Exception("REF not loaded")
        return self._ref

    def set_ref(self, ref: T):
        self._ref = ref
        self._ref_loaded = True


class OneToMany(GenericModel, Generic[T]):

    _ids: Union[List[int], None] = PrivateAttr(default=None)
    _ids_loaded: bool = PrivateAttr(default=False)

    _refs: Union[List[T], None] = PrivateAttr(default=None)
    _refs_loaded: bool = PrivateAttr(default=False)

    def __init__(self, ids: Union[List[int], None, Unset] = Unset(), refs: Union[List[T], None, Unset] = Unset(), **data):
        super().__init__(**data)

        ids_loaded = not isinstance(ids, Unset)
        refs_loaded = not isinstance(refs, Unset)

        self._ids_loaded = ids_loaded
        self._ids = ids if ids_loaded else None
        self._refs_loaded = refs_loaded
        self._refs = refs if refs_loaded else None

    @property
    def ids(self) -> Union[List[int], None]:
        if not self._ids_loaded:
            raise Exception("IDS are not loaded")
        return self._ids

    @property
    def refs(self) -> Union[List[T], None]:
        if not self._refs_loaded:
            raise Exception("REFS not loaded")
        return self._refs
