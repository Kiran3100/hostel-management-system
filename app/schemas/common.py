"""Common schema models."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Generic message response."""
    
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str
    detail: Optional[str] = None
    status_code: int


class TimestampSchema(BaseModel):
    """Mixin for created_at and updated_at."""
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True