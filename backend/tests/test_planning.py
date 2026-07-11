from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)
HAL = {"Accept": "application/hal+json"}


def venue_payload(external_id: str, name: str, **overrides):
    return {
        "venue_external_id": external_id,
        "venue_name": name,
        "town": "Assen",
        "municipality": "Assen",
        "province": "Drenthe",
        "country": "Netherlands",
        "source_url_primary": "https://example.com/planning-venue",
        "research_status": "researched",
        "confidence_rating": "B",
        "active": True,
        **overrides,
    }


def test_planning_combines_map_calendar_deadline_and_committed_engagement():
    venue_response = client.post(
        "/venues",
        json=venue_payload("VEN-NL-DR-ASSEN-PLANNING", "Mapped square", latitude=52.9928, longitude=6.5642),
    )
    assert venue_response.status_code == 201
    venue = venue_response.json()
    opportunity = client.post(
        "/v1/opportunities",
        headers=HAL,
        json={
            "name": "Planning market",
            "event_date": "2026-09-12",
            "application_deadline": "2026-08-01",
            "application_status": "accepted",
            "profit_score": 82,
            "venue_id": venue["id"],
        },
    ).json()
    engagement_response = client.post(
        "/v1/engagements",
        headers=HAL,
        json={"opportunity_id": opportunity["id"], "status": "committed", "commitment_date": "2026-07-05"},
    )
    assert engagement_response.status_code == 201
    engagement = engagement_response.json()
    assert engagement["_links"]["opportunity"]["href"] == opportunity["_links"]["self"]["href"]
    collection = client.get(
        f"/v1/engagements?opportunity_id={opportunity['id']}", headers=HAL
    ).json()
    assert collection["_embedded"]["engagements"][0]["id"] == engagement["id"]
    assert collection["page"]["total_elements"] == 1

    response = client.get(
        "/v1/planning?date_from=2026-08-01&date_to=2026-09-30&max_distance_km=100&min_score=80",
        headers=HAL,
    )
    assert response.status_code == 200
    result = next(item for item in response.json()["opportunities"] if item["id"] == opportunity["id"])
    assert result["venue"]["latitude"] == 52.9928
    assert 30 < result["distance_km"] < 60
    assert result["profit_score"] == 82
    assert result["engagements"][0]["id"] == engagement["id"]

    excluded = client.get("/v1/planning?min_score=90", headers=HAL)
    assert all(item["id"] != opportunity["id"] for item in excluded.json()["opportunities"])


def test_planning_reports_missing_coordinates_and_dates_and_handles_empty_range():
    opportunity = client.post(
        "/v1/opportunities",
        headers=HAL,
        json={"name": "Unscheduled research lead", "application_status": "researching"},
    ).json()

    response = client.get("/v1/planning", headers=HAL)
    warnings = [item for item in response.json()["warnings"] if item["opportunity_id"] == opportunity["id"]]
    assert {item["code"] for item in warnings} == {"missing_coordinates", "missing_date"}

    invalid = client.get("/v1/planning?date_from=2026-09-01&date_to=2026-08-01", headers=HAL)
    assert invalid.status_code == 200
    assert invalid.json()["opportunities"] == []


def test_engagement_rejects_unknown_opportunity_and_can_be_updated():
    missing = client.post("/v1/engagements", headers=HAL, json={"opportunity_id": 999999})
    assert missing.status_code == 404

    opportunity = client.post(
        "/v1/opportunities", headers=HAL, json={"name": "Engagement lifecycle"}
    ).json()
    created = client.post(
        "/v1/engagements", headers=HAL, json={"opportunity_id": opportunity["id"]}
    ).json()
    updated = client.patch(
        created["_links"]["self"]["href"], headers=HAL, json={"status": "cancelled"}
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "cancelled"
