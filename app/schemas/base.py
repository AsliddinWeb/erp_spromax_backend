from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class BaseSchema(BaseModel):
    """Base Pydantic schema"""
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    """Timestamp fields uchun schema"""
    created_at: datetime
    updated_at: datetime


class BaseIDSchema(TimestampSchema):
    """ID bilan schema"""
    id: UUID
    is_active: bool = True


class PaginationParams(BaseSchema):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Sahifa raqami")
    page_size: int = Field(20, ge=1, le=100, description="Sahifadagi elementlar soni")
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseSchema):
    """Pagination response"""
    total: int = Field(..., description="Jami elementlar soni")
    page: int = Field(..., description="Joriy sahifa")
    page_size: int = Field(..., description="Sahifadagi elementlar soni")
    total_pages: int = Field(..., description="Jami sahifalar soni")
    
    @classmethod
    def create(cls, total: int, page: int, page_size: int):
        """Pagination response yaratish"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )