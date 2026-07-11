from datetime import date, datetime
from decimal import Decimal
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
    series_name: Optional[str] = Field(default=None, max_length=255)


class OpportunitySeriesBase(UTCModel):
    name: str = Field(..., min_length=1, max_length=255)
    active: bool = True


class OpportunitySeriesCreate(OpportunitySeriesBase):
    pass


class OpportunitySeriesUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    active: Optional[bool] = None


class OpportunitySeriesRead(OpportunitySeriesBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class OpportunitySeriesAssignment(BaseModel):
    series_id: Optional[int] = Field(default=None, ge=1, le=2_147_483_647)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)


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
    series_name: Optional[str] = Field(default=None, max_length=255)


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


class EngagementBase(UTCModel):
    opportunity_id: int = Field(ge=1, le=2_147_483_647)
    status: str = Field(default="committed", min_length=1, max_length=50)
    commitment_date: Optional[date] = None
    pitch_number: Optional[str] = Field(default=None, max_length=100)
    setup_start_at: Optional[datetime] = None
    setup_end_at: Optional[datetime] = None
    teardown_start_at: Optional[datetime] = None
    teardown_end_at: Optional[datetime] = None
    arrival_plan: Optional[str] = None
    staffing_notes: Optional[str] = None
    equipment_notes: Optional[str] = None
    inventory_notes: Optional[str] = None
    travel_notes: Optional[str] = None
    calendar_visibility: bool = True
    notes: Optional[str] = None
    attended: bool = True
    revenue_eur: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    costs_eur: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    weather_notes: Optional[str] = None
    best_selling_items: Optional[str] = None
    operational_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    attend_again: Optional[bool] = None
    lessons_learned: Optional[str] = None


class EngagementCreate(EngagementBase):
    pass


class EngagementUpdate(BaseModel):
    status: Optional[str] = Field(default=None, min_length=1, max_length=50)
    commitment_date: Optional[date] = None
    pitch_number: Optional[str] = Field(default=None, max_length=100)
    setup_start_at: Optional[datetime] = None
    setup_end_at: Optional[datetime] = None
    teardown_start_at: Optional[datetime] = None
    teardown_end_at: Optional[datetime] = None
    arrival_plan: Optional[str] = None
    staffing_notes: Optional[str] = None
    equipment_notes: Optional[str] = None
    inventory_notes: Optional[str] = None
    travel_notes: Optional[str] = None
    calendar_visibility: Optional[bool] = None
    notes: Optional[str] = None
    attended: Optional[bool] = None
    revenue_eur: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    costs_eur: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    weather_notes: Optional[str] = None
    best_selling_items: Optional[str] = None
    operational_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    attend_again: Optional[bool] = None
    lessons_learned: Optional[str] = None


class EngagementRead(EngagementBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profit_eur: Decimal
    created_at: datetime
    updated_at: datetime
