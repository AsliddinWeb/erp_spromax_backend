from typing import TypeVar, Generic, List
from pydantic import BaseModel
from app.schemas.base import PaginatedResponse

T = TypeVar('T')


class PaginatedResult(BaseModel, Generic[T]):
    """Paginated natija"""
    items: List[T]
    pagination: PaginatedResponse
    
    class Config:
        arbitrary_types_allowed = True


def paginate(
    items: List[T],
    total: int,
    page: int,
    page_size: int
) -> PaginatedResult[T]:
    """Pagination qilish"""
    pagination = PaginatedResponse.create(
        total=total,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResult(
        items=items,
        pagination=pagination
    )