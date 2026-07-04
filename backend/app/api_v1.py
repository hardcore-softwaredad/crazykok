from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
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
from .opportunity_service import SORT_COLUMNS, filtered_opportunities, ordered_opportunities
from .schemas import OpportunityCreate, OpportunityRead, OpportunityUpdate
from .venue_schemas import VenueRead
from .venue_service import venue_to_dict


router = APIRouter(prefix="/v1", default_response_class=HALJSONResponse, tags=["API v1"])

PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


class OpportunityHAL(OpportunityRead):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    links: dict[str, HALLink | list[HALLink]] = Field(alias="_links")


class OpportunityEmbedded(HALModel):
    opportunities: list[OpportunityHAL]


class OpportunityCollection(HALCollection):
    embedded: OpportunityEmbedded = Field(alias="_embedded")


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
    return links


def opportunity_resource(request: Request, opportunity: models.Opportunity) -> OpportunityHAL:
    data = OpportunityRead.model_validate(opportunity).model_dump()
    return OpportunityHAL(**data, links=opportunity_links(request, opportunity))


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
            "opportunity-search": HALLink(
                href=(
                    f"{api_url(request, 'opportunities')}"
                    "{?q,status,category,location,organizer,venue_id,active,sort,direction,page,page_size}"
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
            "documentation": HALLink(href=f"{api_url(request).removesuffix('/v1')}/docs"),
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
    venue_id: int | None = Query(default=None, ge=1),
    active: bool | None = Query(default=True),
    sort: str = Query(default="event_date"),
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
    record = models.Opportunity(**opportunity.model_dump())
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


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityHAL, response_model_exclude_none=True, name="api-v1-get-opportunity")
def get_opportunity(request: Request, opportunity_id: int, db: Session = Depends(get_db)) -> OpportunityHAL:
    return opportunity_resource(request, get_opportunity_or_404(db, opportunity_id))


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityHAL, response_model_exclude_none=True, name="api-v1-update-opportunity")
def update_opportunity(
    request: Request,
    opportunity_id: int,
    changes: OpportunityUpdate,
    db: Session = Depends(get_db),
) -> OpportunityHAL:
    record = get_opportunity_or_404(db, opportunity_id)
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return opportunity_resource(request, record)


@router.delete("/opportunities/{opportunity_id}", status_code=204, name="api-v1-delete-opportunity")
def delete_opportunity(opportunity_id: int, db: Session = Depends(get_db)) -> Response:
    record = get_opportunity_or_404(db, opportunity_id)
    db.delete(record)
    db.commit()
    return Response(status_code=204)


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
def get_organizer(request: Request, organizer_id: int, db: Session = Depends(get_db)) -> OrganizerHAL:
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
def get_venue(request: Request, venue_id: int, db: Session = Depends(get_db)) -> VenueHAL:
    venue = db.query(models.Venue).filter(models.Venue.id == venue_id).first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue_resource(request, venue)
