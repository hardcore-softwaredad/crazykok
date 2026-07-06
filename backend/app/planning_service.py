from __future__ import annotations

import math
import os
from datetime import date

from sqlalchemy.orm import Session, joinedload

from . import models


HOME_LATITUDE = float(os.getenv("PLANNING_HOME_LATITUDE", "52.6627"))
HOME_LONGITUDE = float(os.getenv("PLANNING_HOME_LONGITUDE", "6.8847"))


def straight_line_distance_km(latitude: float | None, longitude: float | None) -> float | None:
    if latitude is None or longitude is None:
        return None
    radius_km = 6371.0088
    lat1, lat2 = math.radians(HOME_LATITUDE), math.radians(latitude)
    delta_lat = math.radians(latitude - HOME_LATITUDE)
    delta_lon = math.radians(longitude - HOME_LONGITUDE)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return round(radius_km * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value)), 1)


def planning_opportunities(
    db: Session,
    *,
    date_from: date | None,
    date_to: date | None,
    max_distance_km: float | None,
    status: str | None,
    min_score: float | None,
) -> tuple[list[models.Opportunity], list[dict[str, int | str]]]:
    query = (
        db.query(models.Opportunity)
        .options(joinedload(models.Opportunity.venue), joinedload(models.Opportunity.operations))
        .filter(models.Opportunity.is_active.is_(True))
    )
    if min_score is not None:
        query = query.filter(models.Opportunity.profit_score >= min_score)

    candidates = query.order_by(models.Opportunity.event_date.asc().nulls_last(), models.Opportunity.id).all()
    warnings: list[dict[str, int | str]] = []
    selected: list[models.Opportunity] = []
    for opportunity in candidates:
        status_matches = status is None or opportunity.application_status == status or any(
            operation.status == status for operation in opportunity.operations
        )
        if not status_matches:
            continue

        venue = opportunity.venue
        distance = straight_line_distance_km(
            venue.latitude if venue else None,
            venue.longitude if venue else None,
        )
        if distance is None:
            warnings.append(
                {"code": "missing_coordinates", "opportunity_id": opportunity.id, "title": opportunity.name}
            )
        if opportunity.event_date is None:
            warnings.append({"code": "missing_date", "opportunity_id": opportunity.id, "title": opportunity.name})

        if max_distance_km is not None and (distance is None or distance > max_distance_km):
            continue

        dates = [item for item in (opportunity.event_date, opportunity.application_deadline) if item is not None]
        in_range = [
            item
            for item in dates
            if (date_from is None or item >= date_from) and (date_to is None or item <= date_to)
        ]
        if (date_from is not None or date_to is not None) and not in_range:
            continue
        selected.append(opportunity)
    return selected, warnings
