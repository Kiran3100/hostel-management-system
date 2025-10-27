"""Notice schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.notice import NoticePriority
from app.schemas.common import TimestampSchema


class NoticeBase(BaseModel):
    """Base notice schema."""
    
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    priority: NoticePriority = NoticePriority.NORMAL


class NoticeCreate(NoticeBase):
    """Create notice."""
    
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NoticeUpdate(BaseModel):
    """Update notice."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    priority: Optional[NoticePriority] = None
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NoticeResponse(NoticeBase, TimestampSchema):
    """Notice response."""
    
    id: int
    hostel_id: int
    author_id: int
    published_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True