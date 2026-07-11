from __future__ import annotations

from datetime import timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from . import models


def validate_engagement_schedule(engagement: models.Engagement) -> None:
    def comparable(value):
        if value is not None and value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    pairs = (
        (engagement.setup_start_at, engagement.setup_end_at, "Setup end must be after setup start"),
        (engagement.teardown_start_at, engagement.teardown_end_at, "Teardown end must be after teardown start"),
    )
    for start, end, message in pairs:
        start, end = comparable(start), comparable(end)
        if start is not None and end is not None and end < start:
            raise HTTPException(status_code=422, detail=message)


def update_engagement_profit(engagement: models.Engagement) -> None:
    engagement.profit_eur = Decimal(engagement.revenue_eur or 0) - Decimal(engagement.costs_eur or 0)


def apply_engagement_values(engagement: models.Engagement, values: dict) -> None:
    for field, value in values.items():
        setattr(engagement, field, value)
    update_engagement_profit(engagement)
    validate_engagement_schedule(engagement)


def comparison_rows(db: Session, group_by: str) -> list[dict]:
    engagements = (
        db.query(models.Engagement)
        .options(joinedload(models.Engagement.opportunity).joinedload(models.Opportunity.venue))
        .filter(models.Engagement.status == "completed")
        .all()
    )
    grouped: dict[str, dict[int, dict[str, Decimal | int]]] = {}
    for engagement in engagements:
        opportunity = engagement.opportunity
        venue = opportunity.venue
        if opportunity.event_date is None:
            continue
        if group_by == "series":
            key = opportunity.series.name if opportunity.series else opportunity.name
        elif group_by == "venue":
            key = venue.venue_name if venue else "Unknown venue"
        elif group_by == "organizer":
            key = opportunity.organizer or "Unknown organizer"
        else:
            key = venue.municipality if venue and venue.municipality else "Unknown municipality"
        year = opportunity.event_date.year
        bucket = grouped.setdefault(key, {}).setdefault(
            year,
            {"engagement_count": 0, "revenue_eur": Decimal("0"), "costs_eur": Decimal("0"), "profit_eur": Decimal("0")},
        )
        bucket["engagement_count"] += 1
        bucket["revenue_eur"] += engagement.revenue_eur
        bucket["costs_eur"] += engagement.costs_eur
        bucket["profit_eur"] += engagement.profit_eur
    return [
        {
            "group": key,
            "years": [{"year": year, **totals} for year, totals in sorted(years.items(), reverse=True)],
        }
        for key, years in sorted(grouped.items())
    ]
