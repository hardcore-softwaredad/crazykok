from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from pydantic import ConfigDict, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .hypermedia import (
    HALCollection,
    HALJSONResponse,
    HALLink,
    HALModel,
    HALResource,
    Page,
    api_url,
    pagination_links,
)
from .engagement_service import apply_engagement_values, comparison_rows
from .opportunity_service import SORT_COLUMNS, apply_opportunity_values, filtered_opportunities, ordered_opportunities
from .openapi_contract import api_docs_origin
from .planning_service import planning_opportunities, straight_line_distance_km
from .schemas import (
    EngagementCreate,
    EngagementRead,
    EngagementUpdate,
    OpportunityCreate,
    OpportunityRead,
    OpportunitySeriesAssignment,
    OpportunitySeriesCreate,
    OpportunitySeriesRead,
    OpportunitySeriesUpdate,
    OpportunityUpdate,
)
from .venue_schemas import VenueRead
from .venue_service import venue_to_dict


router = APIRouter(prefix="/v1", default_response_class=HALJSONResponse, tags=["API v1"])

PageNumber = Annotated[int, Query(ge=1, le=1_000_000)]
PageSize = Annotated[int, Query(ge=1, le=100)]
DatabaseID = Annotated[int, Path(ge=1, le=2_147_483_647)]
OpportunitySort = Literal[
    "event_date",
    "application_deadline",
    "name",
    "location",
    "category",
    "application_status",
    "expected_revenue",
    "expected_attendance",
    "profit_score",
]


class OpportunityHAL(OpportunityRead):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    links: dict[str, HALLink | list[HALLink]] = Field(alias="_links")


class OpportunitySeriesHAL(OpportunitySeriesRead):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    links: dict[str, HALLink] = Field(alias="_links")
    opportunity_count: int = 0


class OpportunitySeriesEmbedded(HALModel):
    series: list[OpportunitySeriesHAL]


class OpportunitySeriesCollection(HALCollection):
    embedded: OpportunitySeriesEmbedded = Field(alias="_embedded")


class OpportunityEmbedded(HALModel):
    opportunities: list[OpportunityHAL]


class OpportunityCollection(HALCollection):
    embedded: OpportunityEmbedded = Field(alias="_embedded")


class EngagementHAL(EngagementRead):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    links: dict[str, HALLink] = Field(alias="_links")
    opportunity_name: str
    event_date: date | None = None


class EngagementEmbedded(HALModel):
    engagements: list[EngagementHAL]


class EngagementCollection(HALCollection):
    embedded: EngagementEmbedded = Field(alias="_embedded")


class ComparisonYear(HALModel):
    year: int
    engagement_count: int
    revenue_eur: Decimal
    costs_eur: Decimal
    profit_eur: Decimal


class ComparisonGroup(HALModel):
    group: str
    years: list[ComparisonYear]


class ComparisonResponse(HALResource):
    group_by: Literal["series", "venue", "organizer", "municipality"]
    groups: list[ComparisonGroup]


class PlanningVenue(HALModel):
    id: int
    name: str
    latitude: float | None = None
    longitude: float | None = None


class PlanningEngagement(HALModel):
    id: int
    status: str
    commitment_date: date | None = None
    links: dict[str, HALLink] = Field(alias="_links")


class PlanningOpportunity(HALModel):
    id: int
    name: str
    event_date: date | None = None
    application_deadline: date | None = None
    application_status: str
    profit_score: float | None = None
    distance_km: float | None = None
    venue: PlanningVenue | None = None
    engagements: list[PlanningEngagement]
    links: dict[str, HALLink] = Field(alias="_links")


class PlanningWarning(HALModel):
    code: Literal["missing_coordinates", "missing_date"]
    opportunity_id: int
    title: str


class PlanningResponse(HALResource):
    opportunities: list[PlanningOpportunity]
    warnings: list[PlanningWarning]


class OrganizerHAL(HALResource):
    id: int
    name: str
    contact_email: str | None = None
    phone: str | None = None
    notes: str | None = None


class OrganizerEmbedded(HALModel):
    organizers: list[OrganizerHAL]


class OrganizerCollection(HALCollection):
    embedded: OrganizerEmbedded = Field(alias="_embedded")


class VenueHAL(VenueRead):
    model_config = ConfigDict(extra="forbid", from_attributes=True, populate_by_name=True)

    links: dict[str, HALLink | list[HALLink]] = Field(alias="_links")


class VenueEmbedded(HALModel):
    venues: list[VenueHAL]


class VenueCollection(HALCollection):
    embedded: VenueEmbedded = Field(alias="_embedded")


class APIRoot(HALResource):
    version: str


def opportunity_links(request: Request, opportunity: models.Opportunity) -> dict[str, HALLink]:
    links = {
        "self": HALLink(href=api_url(request, f"opportunities/{opportunity.id}")),
        "collection": HALLink(href=api_url(request, "opportunities")),
    }
    if opportunity.venue_id is not None:
        links["venue"] = HALLink(href=api_url(request, f"venues/{opportunity.venue_id}"))
    if opportunity.opportunity_series_id is not None:
        links["series"] = HALLink(href=api_url(request, f"opportunity-series/{opportunity.opportunity_series_id}"))
    links["engagements"] = HALLink(
        href=api_url(request, "engagements", [("opportunity_id", opportunity.id)])
    )
    links["series-assignment"] = HALLink(href=api_url(request, f"opportunities/{opportunity.id}/series"))
    return links


def opportunity_resource(request: Request, opportunity: models.Opportunity) -> OpportunityHAL:
    data = OpportunityRead.model_validate(opportunity).model_dump()
    return OpportunityHAL(**data, links=opportunity_links(request, opportunity))


def series_links(request: Request, series: models.OpportunitySeries) -> dict[str, HALLink]:
    return {
        "self": HALLink(href=api_url(request, f"opportunity-series/{series.id}")),
        "collection": HALLink(href=api_url(request, "opportunity-series")),
        "opportunities": HALLink(href=api_url(request, "opportunities", [("series_id", series.id)])),
    }


def series_resource(request: Request, series: models.OpportunitySeries) -> OpportunitySeriesHAL:
    data = OpportunitySeriesRead.model_validate(series).model_dump()
    return OpportunitySeriesHAL(
        **data,
        opportunity_count=len(series.opportunities),
        links=series_links(request, series),
    )


def organizer_resource(request: Request, organizer: models.Organizer) -> OrganizerHAL:
    return OrganizerHAL(
        id=organizer.id,
        name=organizer.name,
        contact_email=organizer.contact_email,
        phone=organizer.phone,
        notes=organizer.notes,
        links={
            "self": HALLink(href=api_url(request, f"organizers/{organizer.id}")),
            "collection": HALLink(href=api_url(request, "organizers")),
            "opportunities": HALLink(
                href=api_url(request, "opportunities", [("organizer", organizer.name)])
            ),
        },
    )


def venue_resource(request: Request, venue: models.Venue) -> VenueHAL:
    return VenueHAL(
        **venue_to_dict(venue),
        links={
            "self": HALLink(href=api_url(request, f"venues/{venue.id}")),
            "collection": HALLink(href=api_url(request, "venues")),
            "opportunities": HALLink(
                href=api_url(request, "opportunities", [("venue_id", venue.id)])
            ),
        },
    )


@router.get("", response_model=APIRoot, response_model_exclude_none=True, name="api-v1-root")
def api_root(request: Request) -> APIRoot:
    return APIRoot(
        version="1",
        links={
            "self": HALLink(href=api_url(request)),
            "opportunities": HALLink(href=api_url(request, "opportunities")),
            "opportunity-series": HALLink(href=api_url(request, "opportunity-series")),
            "engagements": HALLink(href=api_url(request, "engagements")),
            "engagement-comparisons": HALLink(
                href=f"{api_url(request, 'engagements/comparisons')}{{?group_by}}",
                templated=True,
            ),
            "planning": HALLink(
                href=(
                    f"{api_url(request, 'planning')}"
                    "{?date_from,date_to,max_distance_km,status,min_score}"
                ),
                templated=True,
            ),
            "opportunity-search": HALLink(
                href=(
                    f"{api_url(request, 'opportunities')}"
                    "{?q,status,category,location,organizer,venue_id,series_id,active,sort,direction,page,page_size}"
                ),
                templated=True,
            ),
            "organizers": HALLink(href=api_url(request, "organizers")),
            "venues": HALLink(href=api_url(request, "venues")),
            "venue-search": HALLink(
                href=(
                    f"{api_url(request, 'venues')}"
                    "{?q,town,municipality,category,research_status,confidence,active,missing_coordinates,page,page_size}"
                ),
                templated=True,
            ),
            "api-description": HALLink(href=api_url(request, "api-description")),
            "documentation": HALLink(href=api_docs_origin()),
        },
    )


@router.get("/opportunities", response_model=OpportunityCollection, response_model_exclude_none=True, name="api-v1-list-opportunities")
def list_opportunities(
    request: Request,
    q: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None, max_length=50),
    category: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=255),
    organizer: str | None = Query(default=None, max_length=255),
    venue_id: int | None = Query(default=None, ge=1, le=2_147_483_647),
    series_id: int | None = Query(default=None, ge=1, le=2_147_483_647),
    active: bool | None = Query(default=True),
    sort: OpportunitySort = Query(default="event_date"),
    direction: str = Query(default="asc", pattern="^(asc|desc)$"),
    page: PageNumber = 1,
    page_size: PageSize = 25,
    db: Session = Depends(get_db),
) -> OpportunityCollection:
    if sort not in SORT_COLUMNS:
        raise HTTPException(status_code=422, detail=f"Unsupported sort field: {sort}")

    filtered = filtered_opportunities(
        db,
        q=q,
        status=status,
        category=category,
        location=location,
        organizer=organizer,
        venue_id=venue_id,
        series_id=series_id,
        active=active,
    )
    total = filtered.count()
    records = (
        ordered_opportunities(filtered, sort, direction)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    page_data = Page(number=page, size=page_size, total_elements=total)
    query: list[tuple[str, str | int | bool]] = []
    for key, value in (
        ("q", q),
        ("status", status),
        ("category", category),
        ("location", location),
        ("organizer", organizer),
        ("venue_id", venue_id),
        ("series_id", series_id),
        ("active", active),
    ):
        if value is not None:
            query.append((key, value))
    query.extend([("sort", sort), ("direction", direction), ("page_size", page_size)])
    return OpportunityCollection(
        links=pagination_links(request, "opportunities", query, page_data),
        page=page_data.metadata(),
        embedded=OpportunityEmbedded(
            opportunities=[opportunity_resource(request, record) for record in records]
        ),
    )


@router.post("/opportunities", response_model=OpportunityHAL, response_model_exclude_none=True, status_code=201, name="api-v1-create-opportunity")
def create_opportunity(
    request: Request,
    response: Response,
    opportunity: OpportunityCreate,
    db: Session = Depends(get_db),
) -> OpportunityHAL:
    record = models.Opportunity()
    apply_opportunity_values(db, record, opportunity.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    resource = opportunity_resource(request, record)
    response.headers["Location"] = resource.links["self"].href
    return resource


def get_opportunity_or_404(db: Session, opportunity_id: int) -> models.Opportunity:
    record = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return record


def get_series_or_404(db: Session, series_id: int) -> models.OpportunitySeries:
    record = db.query(models.OpportunitySeries).filter(models.OpportunitySeries.id == series_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Opportunity series not found")
    return record


def find_or_create_series(db: Session, name: str) -> models.OpportunitySeries:
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(status_code=422, detail="Series name cannot be blank")
    record = db.query(models.OpportunitySeries).filter(models.OpportunitySeries.name == cleaned).first()
    if record is None:
        record = models.OpportunitySeries(name=cleaned)
        db.add(record)
        db.flush()
    return record


@router.get(
    "/opportunity-series",
    response_model=OpportunitySeriesCollection,
    response_model_exclude_none=True,
    name="api-v1-list-opportunity-series",
)
def list_opportunity_series(
    request: Request,
    active: bool | None = Query(default=True),
    page: PageNumber = 1,
    page_size: PageSize = 25,
    db: Session = Depends(get_db),
) -> OpportunitySeriesCollection:
    query = db.query(models.OpportunitySeries)
    if active is not None:
        query = query.filter(models.OpportunitySeries.active == active)
    total = query.count()
    records = (
        query.order_by(models.OpportunitySeries.name.asc(), models.OpportunitySeries.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    page_data = Page(number=page, size=page_size, total_elements=total)
    query_params: list[tuple[str, str | int | bool]] = [("page_size", page_size)]
    if active is not None:
        query_params.append(("active", active))
    return OpportunitySeriesCollection(
        links=pagination_links(request, "opportunity-series", query_params, page_data),
        page=page_data.metadata(),
        embedded=OpportunitySeriesEmbedded(series=[series_resource(request, item) for item in records]),
    )


@router.post(
    "/opportunity-series",
    response_model=OpportunitySeriesHAL,
    response_model_exclude_none=True,
    status_code=201,
    name="api-v1-create-opportunity-series",
)
def create_opportunity_series(
    request: Request,
    response: Response,
    payload: OpportunitySeriesCreate,
    db: Session = Depends(get_db),
) -> OpportunitySeriesHAL:
    if db.query(models.OpportunitySeries).filter(models.OpportunitySeries.name == payload.name.strip()).first():
        raise HTTPException(status_code=409, detail="Opportunity series already exists")
    record = models.OpportunitySeries(name=payload.name.strip(), active=payload.active)
    db.add(record)
    db.commit()
    db.refresh(record)
    resource = series_resource(request, record)
    response.headers["Location"] = resource.links["self"].href
    return resource


@router.get(
    "/opportunity-series/{series_id}",
    response_model=OpportunitySeriesHAL,
    response_model_exclude_none=True,
    name="api-v1-get-opportunity-series",
)
def get_opportunity_series(request: Request, series_id: DatabaseID, db: Session = Depends(get_db)) -> OpportunitySeriesHAL:
    return series_resource(request, get_series_or_404(db, series_id))


@router.patch(
    "/opportunity-series/{series_id}",
    response_model=OpportunitySeriesHAL,
    response_model_exclude_none=True,
    name="api-v1-update-opportunity-series",
)
def update_opportunity_series(
    request: Request,
    series_id: DatabaseID,
    payload: OpportunitySeriesUpdate,
    db: Session = Depends(get_db),
) -> OpportunitySeriesHAL:
    record = get_series_or_404(db, series_id)
    values = payload.model_dump(exclude_unset=True)
    if "name" in values:
        name = values["name"].strip()
        duplicate = db.query(models.OpportunitySeries).filter(
            models.OpportunitySeries.name == name,
            models.OpportunitySeries.id != series_id,
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Opportunity series already exists")
        record.name = name
        values.pop("name")
    for field, value in values.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return series_resource(request, record)


@router.delete("/opportunity-series/{series_id}", status_code=204, name="api-v1-delete-opportunity-series")
def delete_opportunity_series(series_id: DatabaseID, db: Session = Depends(get_db)) -> Response:
    db.delete(get_series_or_404(db, series_id))
    db.commit()
    return Response(status_code=204)


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityHAL, response_model_exclude_none=True, name="api-v1-get-opportunity")
def get_opportunity(request: Request, opportunity_id: DatabaseID, db: Session = Depends(get_db)) -> OpportunityHAL:
    return opportunity_resource(request, get_opportunity_or_404(db, opportunity_id))


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityHAL, response_model_exclude_none=True, name="api-v1-update-opportunity")
def update_opportunity(
    request: Request,
    opportunity_id: DatabaseID,
    changes: OpportunityUpdate,
    db: Session = Depends(get_db),
) -> OpportunityHAL:
    record = get_opportunity_or_404(db, opportunity_id)
    apply_opportunity_values(db, record, changes.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return opportunity_resource(request, record)


@router.delete("/opportunities/{opportunity_id}", status_code=204, name="api-v1-delete-opportunity")
def delete_opportunity(opportunity_id: DatabaseID, db: Session = Depends(get_db)) -> Response:
    record = get_opportunity_or_404(db, opportunity_id)
    db.delete(record)
    db.commit()
    return Response(status_code=204)


@router.put(
    "/opportunities/{opportunity_id}/series",
    response_model=OpportunityHAL,
    response_model_exclude_none=True,
    name="api-v1-assign-opportunity-series",
)
def assign_opportunity_series(
    request: Request,
    opportunity_id: DatabaseID,
    payload: OpportunitySeriesAssignment,
    db: Session = Depends(get_db),
) -> OpportunityHAL:
    opportunity = get_opportunity_or_404(db, opportunity_id)
    if payload.series_id is None and payload.name is None:
        raise HTTPException(status_code=422, detail="Provide either series_id or name")
    if payload.series_id is not None and payload.name is not None:
        raise HTTPException(status_code=422, detail="Provide only one of series_id or name")
    opportunity.series = get_series_or_404(db, payload.series_id) if payload.series_id else find_or_create_series(db, payload.name or "")
    db.commit()
    db.refresh(opportunity)
    return opportunity_resource(request, opportunity)


@router.post(
    "/opportunities/{opportunity_id}/series",
    response_model=OpportunityHAL,
    response_model_exclude_none=True,
    status_code=201,
    name="api-v1-create-series-from-opportunity",
)
def create_series_from_opportunity(
    request: Request,
    opportunity_id: DatabaseID,
    payload: OpportunitySeriesAssignment | None = None,
    db: Session = Depends(get_db),
) -> OpportunityHAL:
    opportunity = get_opportunity_or_404(db, opportunity_id)
    name = payload.name if payload and payload.name else opportunity.name
    opportunity.series = find_or_create_series(db, name)
    db.commit()
    db.refresh(opportunity)
    return opportunity_resource(request, opportunity)


@router.delete(
    "/opportunities/{opportunity_id}/series",
    response_model=OpportunityHAL,
    response_model_exclude_none=True,
    name="api-v1-detach-opportunity-series",
)
def detach_opportunity_series(
    request: Request,
    opportunity_id: DatabaseID,
    db: Session = Depends(get_db),
) -> OpportunityHAL:
    opportunity = get_opportunity_or_404(db, opportunity_id)
    opportunity.series = None
    db.commit()
    db.refresh(opportunity)
    return opportunity_resource(request, opportunity)


def engagement_links(request: Request, engagement: models.Engagement) -> dict[str, HALLink]:
    links = {
        "self": HALLink(href=api_url(request, f"engagements/{engagement.id}")),
        "collection": HALLink(href=api_url(request, "engagements")),
        "opportunity": HALLink(href=api_url(request, f"opportunities/{engagement.opportunity_id}")),
    }
    return links


def engagement_resource(request: Request, engagement: models.Engagement) -> EngagementHAL:
    data = EngagementRead.model_validate(engagement).model_dump()
    return EngagementHAL(
        **data,
        opportunity_name=engagement.opportunity.name,
        event_date=engagement.opportunity.event_date,
        links=engagement_links(request, engagement),
    )


def get_engagement_or_404(db: Session, engagement_id: int) -> models.Engagement:
    record = db.query(models.Engagement).filter(models.Engagement.id == engagement_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return record


@router.get("/engagements", response_model=EngagementCollection, response_model_exclude_none=True, name="api-v1-list-engagements")
def list_engagements(
    request: Request,
    opportunity_id: int | None = Query(default=None, ge=1, le=2_147_483_647),
    page: PageNumber = 1,
    page_size: PageSize = 25,
    db: Session = Depends(get_db),
) -> EngagementCollection:
    query = db.query(models.Engagement)
    if opportunity_id is not None:
        query = query.filter(models.Engagement.opportunity_id == opportunity_id)
    total = query.count()
    records = query.order_by(models.Engagement.id).offset((page - 1) * page_size).limit(page_size).all()
    page_data = Page(page, page_size, total)
    query_params: list[tuple[str, str | int | bool]] = []
    if opportunity_id is not None:
        query_params.append(("opportunity_id", opportunity_id))
    query_params.append(("page_size", page_size))
    return EngagementCollection(
        links=pagination_links(request, "engagements", query_params, page_data),
        page=page_data.metadata(),
        embedded=EngagementEmbedded(
            engagements=[engagement_resource(request, record) for record in records]
        ),
    )


@router.post("/engagements", response_model=EngagementHAL, response_model_exclude_none=True, status_code=201, name="api-v1-create-engagement")
def create_engagement(
    request: Request,
    response: Response,
    engagement: EngagementCreate,
    db: Session = Depends(get_db),
) -> EngagementHAL:
    get_opportunity_or_404(db, engagement.opportunity_id)
    record = models.Engagement()
    apply_engagement_values(record, engagement.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    resource = engagement_resource(request, record)
    response.headers["Location"] = resource.links["self"].href
    return resource


@router.get(
    "/engagements/comparisons",
    response_model=ComparisonResponse,
    response_model_exclude_none=True,
    name="api-v1-engagement-comparisons",
)
def engagement_comparisons(
    request: Request,
    group_by: Literal["series", "venue", "organizer", "municipality"] = "series",
    db: Session = Depends(get_db),
) -> ComparisonResponse:
    return ComparisonResponse(
        group_by=group_by,
        groups=[ComparisonGroup(**row) for row in comparison_rows(db, group_by)],
        links={
            "self": HALLink(href=api_url(request, "engagements/comparisons", [("group_by", group_by)])),
            "collection": HALLink(href=api_url(request, "engagements")),
        },
    )


@router.get("/engagements/{engagement_id}", response_model=EngagementHAL, response_model_exclude_none=True, name="api-v1-get-engagement")
def get_engagement(request: Request, engagement_id: DatabaseID, db: Session = Depends(get_db)) -> EngagementHAL:
    return engagement_resource(request, get_engagement_or_404(db, engagement_id))


@router.patch("/engagements/{engagement_id}", response_model=EngagementHAL, response_model_exclude_none=True, name="api-v1-update-engagement")
def update_engagement(
    request: Request,
    engagement_id: DatabaseID,
    changes: EngagementUpdate,
    db: Session = Depends(get_db),
) -> EngagementHAL:
    record = get_engagement_or_404(db, engagement_id)
    apply_engagement_values(record, changes.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return engagement_resource(request, record)


@router.delete("/engagements/{engagement_id}", status_code=204, name="api-v1-delete-engagement")
def delete_engagement(engagement_id: DatabaseID, db: Session = Depends(get_db)) -> Response:
    db.delete(get_engagement_or_404(db, engagement_id))
    db.commit()
    return Response(status_code=204)


@router.get("/planning", response_model=PlanningResponse, response_model_exclude_none=True, name="api-v1-planning")
def get_planning(
    request: Request,
    date_from: date | None = None,
    date_to: date | None = None,
    max_distance_km: float | None = Query(default=None, ge=0, le=20_000),
    status: str | None = Query(default=None, max_length=50),
    min_score: float | None = Query(default=None, ge=0, le=100),
    db: Session = Depends(get_db),
) -> PlanningResponse:
    records, warnings = planning_opportunities(
        db,
        date_from=date_from,
        date_to=date_to,
        max_distance_km=max_distance_km,
        status=status,
        min_score=min_score,
    )
    opportunities = []
    for record in records:
        venue = record.venue
        opportunities.append(
            PlanningOpportunity(
                id=record.id,
                name=record.name,
                event_date=record.event_date,
                application_deadline=record.application_deadline,
                application_status=record.application_status,
                profit_score=record.profit_score,
                distance_km=straight_line_distance_km(
                    venue.latitude if venue else None,
                    venue.longitude if venue else None,
                ),
                venue=(
                    PlanningVenue(
                        id=venue.id,
                        name=venue.venue_name,
                        latitude=venue.latitude,
                        longitude=venue.longitude,
                    )
                    if venue
                    else None
                ),
                engagements=[
                    PlanningEngagement(
                        id=engagement.id,
                        status=engagement.status,
                        commitment_date=engagement.commitment_date,
                        links=engagement_links(request, engagement),
                    )
                    for engagement in record.engagements
                    if status is None or engagement.status == status
                ],
                links=opportunity_links(request, record),
            )
        )
    self_query: list[tuple[str, str | int | bool]] = []
    for key, value in (
        ("date_from", date_from.isoformat() if date_from else None),
        ("date_to", date_to.isoformat() if date_to else None),
        ("max_distance_km", str(max_distance_km) if max_distance_km is not None else None),
        ("status", status),
        ("min_score", str(min_score) if min_score is not None else None),
    ):
        if value is not None:
            self_query.append((key, value))
    return PlanningResponse(
        opportunities=opportunities,
        warnings=[PlanningWarning(**warning) for warning in warnings],
        links={
            "self": HALLink(href=api_url(request, "planning", self_query)),
            "collection": HALLink(href=api_url(request, "planning")),
        },
    )


@router.get("/organizers", response_model=OrganizerCollection, response_model_exclude_none=True, name="api-v1-list-organizers")
def list_organizers(
    request: Request,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    db: Session = Depends(get_db),
) -> OrganizerCollection:
    query = db.query(models.Organizer)
    total = query.count()
    records = (
        query.order_by(models.Organizer.name.asc(), models.Organizer.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    page_data = Page(page, page_size, total)
    return OrganizerCollection(
        links=pagination_links(request, "organizers", [("page_size", page_size)], page_data),
        page=page_data.metadata(),
        embedded=OrganizerEmbedded(
            organizers=[organizer_resource(request, item) for item in records]
        ),
    )


@router.get("/organizers/{organizer_id}", response_model=OrganizerHAL, response_model_exclude_none=True, name="api-v1-get-organizer")
def get_organizer(request: Request, organizer_id: DatabaseID, db: Session = Depends(get_db)) -> OrganizerHAL:
    organizer = db.query(models.Organizer).filter(models.Organizer.id == organizer_id).first()
    if organizer is None:
        raise HTTPException(status_code=404, detail="Organizer not found")
    return organizer_resource(request, organizer)


@router.get("/venues", response_model=VenueCollection, response_model_exclude_none=True, name="api-v1-list-venues")
def list_venues(
    request: Request,
    q: str | None = Query(default=None, max_length=150),
    town: str | None = None,
    municipality: str | None = None,
    category: str | None = None,
    research_status: str | None = None,
    confidence: str | None = None,
    active: bool | None = Query(default=True),
    missing_coordinates: bool | None = None,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    db: Session = Depends(get_db),
) -> VenueCollection:
    query = db.query(models.Venue)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                models.Venue.venue_name.ilike(pattern),
                models.Venue.venue_external_id.ilike(pattern),
                models.Venue.town.ilike(pattern),
                models.Venue.municipality.ilike(pattern),
                models.Venue.postcode.ilike(pattern),
            )
        )
    if town:
        query = query.filter(models.Venue.town == town)
    if municipality:
        query = query.filter(models.Venue.municipality == municipality)
    if category:
        query = query.filter(models.Venue.venue_category_primary == category)
    if research_status:
        query = query.filter(models.Venue.research_status == research_status)
    if confidence:
        query = query.filter(models.Venue.confidence_rating == confidence)
    if active is not None:
        query = query.filter(models.Venue.active == active)
    if missing_coordinates is True:
        query = query.filter(or_(models.Venue.latitude.is_(None), models.Venue.longitude.is_(None)))
    total = query.count()
    records = (
        query.order_by(models.Venue.venue_name.asc(), models.Venue.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    page_data = Page(page, page_size, total)
    query_params: list[tuple[str, str | int | bool]] = []
    for key, value in (
        ("q", q),
        ("town", town),
        ("municipality", municipality),
        ("category", category),
        ("research_status", research_status),
        ("confidence", confidence),
        ("active", active),
        ("missing_coordinates", missing_coordinates),
    ):
        if value is not None:
            query_params.append((key, value))
    query_params.append(("page_size", page_size))
    return VenueCollection(
        links=pagination_links(request, "venues", query_params, page_data),
        page=page_data.metadata(),
        embedded=VenueEmbedded(venues=[venue_resource(request, item) for item in records]),
    )


@router.get("/venues/{venue_id}", response_model=VenueHAL, name="api-v1-get-venue")
def get_venue(request: Request, venue_id: DatabaseID, db: Session = Depends(get_db)) -> VenueHAL:
    venue = db.query(models.Venue).filter(models.Venue.id == venue_id).first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue_resource(request, venue)
