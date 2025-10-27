"""Mess menu schemas - COMPLETE FIX."""

from datetime import date
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.mess import MealType
from app.schemas.common import TimestampSchema


class MessMenuBase(BaseModel):
    """Base mess menu schema."""
    
    date: date
    meal_type: MealType
    items: List[str] = Field(..., min_length=1)


class MessMenuCreate(MessMenuBase):
    """Create mess menu."""
    pass


class MessMenuUpdate(BaseModel):
    """Update mess menu (only items can be changed)."""
    
    items: List[str] = Field(..., min_length=1)


class MessMenuResponse(TimestampSchema):
    """Mess menu response - COMPLETE FIX."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    hostel_id: int
    date: date
    meal_type: MealType
    items: List[str]
    
    @field_validator('items', mode='before')
    @classmethod
    def extract_items(cls, v):
        """Extract items from nested dict structure."""
        # If it's stored as {"items": ["Rice", "Dal"]}, extract the list
        if isinstance(v, dict) and 'items' in v:
            return v['items']
        # If it's already a list, return as-is
        elif isinstance(v, list):
            return v
        # Fallback
        return []


class MessMenuBulkCreate(BaseModel):
    """Bulk create multiple menus."""
    
    menus: List[MessMenuCreate] = Field(..., min_length=1)


class WeeklyMenuResponse(BaseModel):
    """Weekly menu response."""
    hostel_id: int
    week_start: date
    week_end: date
    weekly_menu: Dict[str, Any] = {}