from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .api_models import UTCModel


class OpportunityBase(UTCModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = None
    event_date: Optional[date] = None
    application_deadline: Optional[date] = None
    organizer: Optional[str] = None
    category: Optional[str] = None
    application_status: str = Field(default="researching", max_length=50)
    source_url: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None
    expected_revenue: Optional[int] = None
    expected_attendance: Optional[int] = None
    profit_score: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: bool = True
    venue_id: Optional[int] = Field(default=None, ge=1, le=2_147_483_647)


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = None
    event_date: Optional[date] = None
    application_deadline: Optional[date] = None
    organizer: Optional[str] = None
    category: Optional[str] = None
    application_status: Optional[str] = Field(default=None, max_length=50)
    source_url: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None
    expected_revenue: Optional[int] = None
    expected_attendance: Optional[int] = None
    profit_score: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    venue_id: Optional[int] = Field(default=None, ge=1, le=2_147_483_647)


class OpportunityRead(OpportunityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# Deprecated source-compatibility names for the unversioned routes.
EventBase = OpportunityBase
EventCreate = OpportunityCreate
EventUpdate = OpportunityUpdate
EventRead = OpportunityRead


class OrganizerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class OperationBase(UTCModel):
    opportunity_id: int = Field(ge=1, le=2_147_483_647)
    status: str = Field(default="committed", min_length=1, max_length=50)
    commitment_date: Optional[date] = None
    notes: Optional[str] = None


class OperationCreate(OperationBase):
    pass


class OperationUpdate(BaseModel):
    status: Optional[str] = Field(default=None, min_length=1, max_length=50)
    commitment_date: Optional[date] = None
    notes: Optional[str] = None


class OperationRead(OperationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
