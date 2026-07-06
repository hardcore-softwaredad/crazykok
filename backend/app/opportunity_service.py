from __future__ import annotations

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query, Session

from . import models


SORT_COLUMNS = {
    "event_date": models.Opportunity.event_date,
    "application_deadline": models.Opportunity.application_deadline,
    "name": models.Opportunity.name,
    "location": models.Opportunity.location,
    "category": models.Opportunity.category,
    "application_status": models.Opportunity.application_status,
    "expected_revenue": models.Opportunity.expected_revenue,
    "expected_attendance": models.Opportunity.expected_attendance,
    "profit_score": models.Opportunity.profit_score,
}


def filtered_opportunities(
    db: Session,
    *,
    q: str | None = None,
    status: str | None = None,
    category: str | None = None,
    location: str | None = None,
    organizer: str | None = None,
    venue_id: int | None = None,
    active: bool | None = True,
) -> Query:
    query = db.query(models.Opportunity)
    if q:
        search = f"%{q}%"
        query = query.filter(
            models.Opportunity.name.ilike(search)
            | models.Opportunity.location.ilike(search)
            | models.Opportunity.organizer.ilike(search)
            | models.Opportunity.category.ilike(search)
            | models.Opportunity.notes.ilike(search)
        )
    if status:
        query = query.filter(models.Opportunity.application_status == status)
    if category:
        query = query.filter(models.Opportunity.category == category)
    if location:
        query = query.filter(models.Opportunity.location.ilike(f"%{location}%"))
    if organizer:
        query = query.filter(models.Opportunity.organizer == organizer)
    if venue_id is not None:
        query = query.filter(models.Opportunity.venue_id == venue_id)
    if active is not None:
        query = query.filter(models.Opportunity.is_active == active)
    return query


def ordered_opportunities(query: Query, sort: str, direction: str) -> Query:
    column = SORT_COLUMNS[sort]
    order = desc(column) if direction == "desc" else asc(column)
    return query.order_by(order.nulls_last(), asc(models.Opportunity.id))
