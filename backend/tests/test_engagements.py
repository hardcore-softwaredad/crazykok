from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)
HAL = {"Accept": "application/hal+json"}


def create_opportunity(name: str, event_date: str, organizer: str = "Market team", venue_id=None, series_name=None):
    payload = {"name": name, "event_date": event_date, "organizer": organizer, "series_name": series_name}
    if venue_id is not None:
        payload["venue_id"] = venue_id
    return client.post("/v1/opportunities", headers=HAL, json=payload).json()


def test_engagement_planning_validates_schedule_and_returns_context():
    opportunity = create_opportunity("Summer Market", "2026-08-12")
    response = client.post(
        "/v1/engagements",
        headers=HAL,
        json={
            "opportunity_id": opportunity["id"],
            "status": "planned",
            "pitch_number": "A-14",
            "setup_start_at": "2026-08-12T08:00:00Z",
            "setup_end_at": "2026-08-12T09:00:00Z",
            "staffing_notes": "Two people",
            "equipment_notes": "Gazebo and griddle",
        },
    )
    assert response.status_code == 201
    assert response.json()["opportunity_name"] == "Summer Market"
    assert response.json()["pitch_number"] == "A-14"
    assert response.json()["profit_eur"] == "0.00"

    invalid = client.patch(
        response.json()["_links"]["self"]["href"],
        headers=HAL,
        json={"setup_end_at": "2026-08-12T07:00:00Z"},
    )
    assert invalid.status_code == 422
    assert "Setup end" in invalid.json()["detail"]


def test_engagement_profit_is_server_calculated_on_update():
    opportunity = create_opportunity("Profit Market", "2026-09-01")
    engagement = client.post(
        "/v1/engagements", headers=HAL, json={"opportunity_id": opportunity["id"]}
    ).json()
    updated = client.patch(
        engagement["_links"]["self"]["href"],
        headers=HAL,
        json={"status": "completed", "revenue_eur": "1300", "costs_eur": "400", "rating": 5},
    )
    assert updated.status_code == 200
    assert float(updated.json()["profit_eur"]) == 900
    assert updated.json()["rating"] == 5


def test_year_comparisons_derive_totals_for_each_supported_dimension():
    venue = client.post(
        "/venues",
        json={
            "venue_external_id": "VEN-NL-DR-ASSEN-COMPARE",
            "venue_name": "Town Square",
            "town": "Assen",
            "municipality": "Assen",
            "province": "Drenthe",
            "country": "Netherlands",
            "source_url_primary": "https://example.com/venue",
            "research_status": "researched",
            "confidence_rating": "B",
            "active": True,
        },
    ).json()
    for year, revenue, costs in ((2025, 1000, 300), (2026, 1400, 350)):
        opportunity = create_opportunity(f"Annual Fair {year}", f"{year}-06-10", venue_id=venue["id"], series_name="Annual Fair")
        client.post(
            "/v1/engagements",
            headers=HAL,
            json={"opportunity_id": opportunity["id"], "status": "completed", "revenue_eur": revenue, "costs_eur": costs},
        )

    series = client.get("/v1/engagements/comparisons?group_by=series", headers=HAL)
    assert series.status_code == 200
    annual = next(group for group in series.json()["groups"] if group["group"] == "Annual Fair")
    assert [row["year"] for row in annual["years"]] == [2026, 2025]
    assert float(annual["years"][0]["profit_eur"]) == 1050
    assert annual["years"][0]["engagement_count"] == 1

    municipality = client.get("/v1/engagements/comparisons?group_by=municipality", headers=HAL)
    assen = next(group for group in municipality.json()["groups"] if group["group"] == "Assen")
    assert len(assen["years"]) == 2


def test_opportunity_series_can_be_managed_and_assigned_from_opportunity():
    opportunity = create_opportunity("Emmen market 2026-08-08", "2026-08-08")

    created = client.post(
        opportunity["_links"]["series-assignment"]["href"],
        headers=HAL,
        json={"name": "Emmen Weekly Market"},
    )
    assert created.status_code == 201
    assert created.json()["series_name"] == "Emmen Weekly Market"

    series_collection = client.get("/v1/opportunity-series", headers=HAL).json()
    series = next(item for item in series_collection["_embedded"]["series"] if item["name"] == "Emmen Weekly Market")
    assert series["opportunity_count"] >= 1

    detached = client.delete(created.json()["_links"]["series-assignment"]["href"], headers=HAL)
    assert detached.status_code == 200
    assert "series_name" not in detached.json()

    assigned = client.put(
        detached.json()["_links"]["series-assignment"]["href"],
        headers=HAL,
        json={"series_id": series["id"]},
    )
    assert assigned.status_code == 200
    assert assigned.json()["series_name"] == "Emmen Weekly Market"
