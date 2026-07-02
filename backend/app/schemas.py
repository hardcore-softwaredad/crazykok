from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = None
    event_date: Optional[date] = None
    organizer: Optional[str] = None
    category: Optional[str] = None
    expected_revenue: Optional[int] = None
    expected_attendance: Optional[int] = None
    is_active: bool = True


class EventCreate(EventBase):
    pass


class EventRead(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizerRead(BaseModel):
    id: int
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class VenueRead(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    capacity: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
