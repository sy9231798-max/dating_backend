from typing import List, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")
class PaginationMeta(BaseModel):
    page: int
    page_item: int
    total: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: PaginationMeta
