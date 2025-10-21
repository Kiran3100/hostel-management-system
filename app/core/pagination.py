"""Pagination utilities."""

from typing import Generic, List, TypeVar, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


class PageResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "PageResponse[T]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


async def paginate(
    db: AsyncSession,
    query,
    pagination: PaginationParams,
    model: Optional[type] = None,
) -> tuple[List, int]:
    """Execute a paginated query.
    
    Returns:
        Tuple of (items, total_count)
    """
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated items
    paginated_query = query.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(paginated_query)
    items = result.scalars().all()
    
    return items, total