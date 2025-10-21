"""Complaint schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_serializer

from app.models.complaint import ComplaintCategory, ComplaintPriority, ComplaintStatus
from app.schemas.common import TimestampSchema


class ComplaintBase(BaseModel):
    """Base complaint schema."""
    
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: ComplaintCategory
    priority: ComplaintPriority = ComplaintPriority.MEDIUM


class ComplaintCreate(ComplaintBase):
    """Create complaint."""
    pass


class ComplaintUpdate(BaseModel):
    """Update complaint (admin)."""
    
    status: Optional[ComplaintStatus] = None
    priority: Optional[ComplaintPriority] = None
    assigned_to: Optional[int] = None
    resolution_notes: Optional[str] = None


class ComplaintResponse(TimestampSchema):
    """Complaint response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    hostel_id: int
    tenant_id: int
    title: str
    description: str
    category: ComplaintCategory
    priority: ComplaintPriority
    status: ComplaintStatus
    assigned_to: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    @field_serializer('category', 'priority', 'status')
    def serialize_enums(self, value):
        """Serialize enum values."""
        if value is not None:
            return value.value if hasattr(value, 'value') else value
        return value


class ComplaintCommentCreate(BaseModel):
    """Create complaint comment."""
    
    comment: str = Field(..., min_length=1)


class ComplaintCommentResponse(TimestampSchema):
    """Complaint comment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    complaint_id: int
    user_id: int
    comment: str