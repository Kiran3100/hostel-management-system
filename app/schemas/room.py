# app/schemas/room.py


"""Room and bed schemas."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.models.room import RoomType
from app.schemas.common import TimestampSchema


class RoomBase(BaseModel):
    """Base room schema."""
    
    number: str = Field(..., min_length=1, max_length=50)
    floor: int = Field(..., ge=0)
    room_type: RoomType
    capacity: int = Field(..., ge=1)
    description: Optional[str] = None
    
    @field_validator('room_type', mode='before')
    @classmethod
    def normalize_room_type(cls, v):
        """Normalize room type to uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v


class RoomCreate(RoomBase):
    """Create room schema."""
    
    hostel_id: int


class RoomUpdate(BaseModel):
    """Update room schema."""
    
    number: Optional[str] = Field(None, min_length=1, max_length=50)
    floor: Optional[int] = Field(None, ge=0)
    room_type: Optional[RoomType] = None
    capacity: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None
    
    @field_validator('room_type', mode='before')
    @classmethod
    def normalize_room_type(cls, v):
        """Normalize room type to uppercase."""
        if v is not None and isinstance(v, str):
            return v.upper()
        return v



class RoomResponse(RoomBase, TimestampSchema):
    """Room response schema."""
    
    id: int
    hostel_id: int
    
    class Config:
        from_attributes = True


class RoomWithBeds(RoomResponse):
    """Room with bed information."""
    
    total_beds: int = 0
    occupied_beds: int = 0
    available_beds: int = 0


class BedBase(BaseModel):
    """Base bed schema."""
    
    number: str = Field(..., min_length=1, max_length=10)


class BedCreate(BedBase):
    """Create bed schema."""
    
    room_id: int


class BedUpdate(BaseModel):
    """Update bed schema."""
    
    number: Optional[str] = Field(None, min_length=1, max_length=10)


class BedResponse(BedBase, TimestampSchema):
    """Bed response schema."""
    
    id: int
    room_id: int
    hostel_id: int
    is_occupied: bool
    tenant_id: Optional[int]
    
    class Config:
        from_attributes = True


class BedAssignRequest(BaseModel):
    """Assign tenant to bed."""
    
    tenant_id: int