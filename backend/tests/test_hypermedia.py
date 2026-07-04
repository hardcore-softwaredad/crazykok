from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)
HAL = "application/hal+json"


def opportunity_payload(name: str) -> dict:
    return {
        "name": name,
        "location": "Assen",
        "application_status": "watchlist",
        "is_active": True,
    }


def test_api_root_is_discoverable_and_proxy_aware():
    response = client.get(
        "/v1",
        headers={
            "Accept": HAL,
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": "crazykok.local",
            "X-Forwarded-Prefix": "/api",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(HAL)
    assert "Accept" in response.headers["vary"]
    assert response.json()["_links"]["self"]["href"] == "https://crazykok.local/api/v1"
    assert response.json()["_links"]["documentation"]["href"] == "https://crazykok.local/api/docs"
    assert response.json()["_links"]["opportunity-search"]["templated"] is True
    assert "/internal" not in str(response.json())


def test_opportunity_resource_and_paginated_collection_contract():
    prefix = f"HAL-{uuid4().hex}"
    created: list[dict] = []
    try:
        for suffix in ("A", "B", "C"):
            response = client.post(
                "/v1/opportunities",
                headers={"Accept": HAL},
                json=opportunity_payload(f"{prefix}-{suffix}"),
            )
            assert response.status_code == 201
            assert response.headers["location"] == response.json()["_links"]["self"]["href"]
            assert response.json()["_links"]["collection"]["href"].endswith("/v1/opportunities")
            created.append(response.json())

        first = client.get(
            f"/v1/opportunities?q={prefix}&page=1&page_size=2&sort=name&direction=asc",
            headers={"Accept": HAL},
        )
        payload = first.json()
        assert first.status_code == 200
        assert payload["page"] == {
            "number": 1,
            "size": 2,
            "total_elements": 3,
            "total_pages": 2,
        }
        assert len(payload["_embedded"]["opportunities"]) == 2
        assert "prev" not in payload["_links"]
        assert "next" in payload["_links"]
        assert f"q={prefix}" in payload["_links"]["next"]["href"]
        assert "sort=name" in payload["_links"]["next"]["href"]

        second = client.get(payload["_links"]["next"]["href"], headers={"Accept": HAL})
        assert second.status_code == 200
        assert second.json()["page"]["number"] == 2
        assert "next" not in second.json()["_links"]
        assert "prev" in second.json()["_links"]

        updated = client.patch(
            created[0]["_links"]["self"]["href"],
            headers={"Accept": HAL},
            json={"application_status": "applied"},
        )
        assert updated.status_code == 200
        assert updated.json()["application_status"] == "applied"
        assert updated.json()["_links"]["self"] == created[0]["_links"]["self"]
    finally:
        for resource in created:
            client.delete(resource["_links"]["self"]["href"], headers={"Accept": HAL})


def test_empty_page_problem_response_and_legacy_deprecation():
    prefix = f"missing-{uuid4().hex}"
    empty = client.get(f"/v1/opportunities?q={prefix}", headers={"Accept": HAL})
    assert empty.status_code == 200
    assert empty.json()["page"]["total_pages"] == 0
    assert empty.json()["_embedded"]["opportunities"] == []
    assert set(empty.json()["_links"]) == {"self"}

    invalid = client.get("/v1/opportunities?page=0", headers={"Accept": HAL})
    assert invalid.status_code == 422
    assert invalid.headers["content-type"].startswith("application/problem+json")
    assert invalid.json()["type"].endswith("validation-error")
    assert invalid.json()["errors"]

    legacy = client.get("/events")
    assert legacy.status_code == 200
    assert legacy.headers["deprecation"] == "true"
    assert "successor-version" in legacy.headers["link"]


def test_openapi_describes_hal_media_type():
    document = client.get("/openapi.json").json()
    content = document["paths"]["/v1/opportunities"]["get"]["responses"]["200"]["content"]
    assert HAL in content
