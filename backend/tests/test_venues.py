import csv
import io
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.venue_registry import VENUE_FIELD_NAMES
from backend.app.venue_registry import VENUE_FIELD_NAMES
from backend.app.venue_service import RELATED_IMPORTS


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def venue_payload(external_id: str, name: str, **overrides):
    return {
        "venue_external_id": external_id,
        "venue_name": name,
        "town": "Assen",
        "municipality": "Assen",
        "province": "Drenthe",
        "country": "Netherlands",
        "source_url_primary": "https://example.com/venue",
        "research_status": "researched",
        "confidence_rating": "B",
        "active": True,
        **overrides,
    }


def csv_bytes(rows: list[dict]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode()


def test_schema_exposes_all_semantic_venue_fields_without_ui_widgets():
    response = client.get("/venues/schema")
    assert response.status_code == 200
    fields = response.json()["fields"]
    assert len(fields) == 111
    assert fields[0]["name"] == "venue_external_id"
    assert "widget" not in fields[0]
    parking = next(field for field in fields if field["name"] == "parking_available")
    assert parking["type"] == "enum"
    assert parking["enum"] == ["yes", "no", "limited", "unknown"]
    research_status = next(field for field in fields if field["name"] == "research_status")
    assert research_status["enum"] == [
        "discovered", "identified", "researched", "verified", "complete", "archived"
    ]


def test_legacy_research_status_values_are_rejected():
    for old_status in ("inventory", "basic"):
        response = client.post(
            "/venues",
            json=venue_payload(f"VEN-NL-DR-ASSEN-{old_status.upper()}", old_status, research_status=old_status),
        )
        assert response.status_code == 422


def test_code_registry_matches_every_canonical_csv_template():
    with (ROOT / "templates" / "venues_import_template.csv").open(newline="") as handle:
        assert tuple(next(csv.reader(handle))) == VENUE_FIELD_NAMES
    for kind, contract in RELATED_IMPORTS.items():
        path = ROOT / "templates" / f"venue_{kind}_import_template.csv"
        with path.open(newline="") as handle:
            assert tuple(next(csv.reader(handle))) == contract["fields"]


def test_venue_crud_filters_archive_and_stable_external_id():
    created = client.post("/venues", json=venue_payload("VEN-NL-DR-ASSEN-MARKT", "Markt Assen"))
    assert created.status_code == 201
    venue = created.json()
    assert venue["town"] == "Assen"
    assert venue["_links"]["self"]["href"].endswith(f"/v1/venues/{venue['id']}")

    updated = client.patch(f"/venues/{venue['id']}", json={"parking_available": "limited"})
    assert updated.status_code == 200
    assert updated.json()["parking_available"] == "limited"

    canonical = client.get(f"/v1/venues/{venue['id']}", headers={"Accept": "application/hal+json"})
    assert canonical.status_code == 200
    assert canonical.json()["parking_available"] == "limited"
    assert set(VENUE_FIELD_NAMES).issubset(canonical.json())
    assert canonical.json()["latitude"] is None
    assert canonical.json()["_links"]["opportunities"]["href"].endswith(
        f"/v1/opportunities?venue_id={venue['id']}"
    )

    immutable = client.patch(f"/venues/{venue['id']}", json={"venue_external_id": "VEN-CHANGED"})
    assert immutable.status_code == 422

    listed = client.get("/venues?q=Markt&research_status=researched")
    assert [item["id"] for item in listed.json()] == [venue["id"]]

    archived = client.post(f"/venues/{venue['id']}/archive")
    assert archived.json()["active"] is False
    assert client.get("/venues").json() == []
    assert client.get("/venues?active=false").json()[0]["id"] == venue["id"]


def test_duplicate_detection_explains_match_signals():
    client.post("/venues", json=venue_payload("VEN-NL-DR-ASSEN-PLEIN", "Koopmansplein", postcode="9401EL"))
    response = client.post(
        "/venues/duplicate-check",
        json={"venue_name": "Koopmans Plein", "town": "Assen", "municipality": "Assen", "postcode": "9401 EL"},
    )
    assert response.status_code == 200
    candidate = response.json()["candidates"][0]
    assert candidate["score"] >= 45
    assert "same postcode" in candidate["signals"]


def test_csv_preview_apply_reimport_and_sparse_update():
    row = venue_payload("VEN-NL-DR-ASSEN-BATCH", "Batch Venue", parking_available="yes")
    content = csv_bytes([row])
    preview = client.post("/venue-imports/preview", files={"venues_file": ("batch.csv", content, "text/csv")})
    assert preview.status_code == 200
    assert preview.json()["rows"][0]["action"] == "create"
    assert client.get("/venues?q=Batch Venue").json() == []

    applied = client.post("/venue-imports/apply", json={"preview_token": preview.json()["preview_token"]})
    assert applied.status_code == 201
    assert applied.json()["counts"]["created"] == 1

    repeated_preview = client.post("/venue-imports/preview", files={"venues_file": ("batch.csv", content, "text/csv")})
    assert repeated_preview.json()["rows"][0]["action"] == "unchanged"
    repeated = client.post("/venue-imports/apply", json={"preview_token": repeated_preview.json()["preview_token"]})
    assert repeated.json()["counts"]["unchanged"] == 1

    sparse = csv_bytes([{"venue_external_id": row["venue_external_id"], "venue_name": row["venue_name"], "parking_available": "limited", "confidence_rating": "B"}])
    sparse_preview = client.post("/venue-imports/preview", files={"venues_file": ("sparse.csv", sparse, "text/csv")})
    changes = sparse_preview.json()["rows"][0]["changes"]
    assert changes == {"parking_available": {"before": "yes", "after": "limited"}}
    result = client.post("/venue-imports/apply", json={"preview_token": sparse_preview.json()["preview_token"]})
    assert result.json()["counts"]["updated"] == 1
    venue = client.get("/venues?q=Batch Venue").json()[0]
    assert venue["parking_available"] == "limited"
    assert venue["town"] == "Assen"


def test_lower_confidence_import_requires_review_and_export_round_trips():
    created = client.post("/venues", json=venue_payload("VEN-NL-DR-ASSEN-CONFIDENCE", "Verified Venue")).json()
    weak = csv_bytes(
        [{
            "venue_external_id": created["venue_external_id"], "venue_name": created["venue_name"],
            "parking_available": "no", "confidence_rating": "D",
        }]
    )
    preview = client.post("/venue-imports/preview", files={"venues_file": ("weak.csv", weak, "text/csv")}).json()
    assert preview["rows"][0]["action"] == "blocked_confidence"
    blocked = client.post("/venue-imports/apply", json={"preview_token": preview["preview_token"]})
    assert blocked.status_code == 409

    preview = client.post("/venue-imports/preview", files={"venues_file": ("weak.csv", weak, "text/csv")}).json()
    overridden = client.post(
        "/venue-imports/apply",
        json={
            "preview_token": preview["preview_token"],
            "resolutions": {"2": {"action": "override", "reason": "Reviewed source manually"}},
        },
    )
    assert overridden.status_code == 201

    exported = client.get(f"/venues/export.csv?ids={created['id']}")
    assert exported.status_code == 200
    assert exported.text.splitlines()[0].startswith("venue_external_id,venue_name,venue_slug")
    round_trip = client.post(
        "/venue-imports/preview", files={"venues_file": ("export.csv", exported.content, "text/csv")}
    )
    assert round_trip.json()["rows"][0]["action"] == "unchanged"


def test_related_records_and_derived_opportunity_history():
    venue = client.post("/venues", json=venue_payload("VEN-NL-DR-ASSEN-RELATED", "Related Venue")).json()
    contact = client.post(
        f"/venues/{venue['id']}/contacts",
        json={"contact_external_id": "CON-RELATED-1", "name": "Booking Desk", "email": "desk@example.com"},
    )
    assert contact.status_code == 201
    assert client.get(f"/venues/{venue['id']}/contacts").json()[0]["name"] == "Booking Desk"

    note = client.post(f"/venues/{venue['id']}/notes", json={"body": "Check loading gate", "origin": "user"})
    assert note.status_code == 201

    opportunity = client.post("/v1/opportunities", json={"name": "Venue Market", "venue_id": venue["id"]})
    assert opportunity.status_code == 201
    history = client.get(f"/venues/{venue['id']}/opportunities").json()
    assert history[0]["name"] == "Venue Market"
    assert client.get(f"/venues/{venue['id']}/statistics").json()["opportunity_count"] == 1


def test_related_csv_is_previewed_and_applied_with_parent_batch():
    venue_row = venue_payload("VEN-NL-DR-ASSEN-WITH-CONTACT", "Venue With Contact")
    contact_row = {
        "contact_external_id": "CON-BATCH-1",
        "venue_external_id": venue_row["venue_external_id"],
        "contact_type": "booking",
        "name": "Batch Contact",
        "email": "batch@example.com",
        "active": "true",
    }
    preview = client.post(
        "/venue-imports/preview",
        files={
            "venues_file": ("venues.csv", csv_bytes([venue_row]), "text/csv"),
            "contacts_file": ("contacts.csv", csv_bytes([contact_row]), "text/csv"),
        },
    )
    assert preview.status_code == 200
    assert preview.json()["related"]["contacts"][0]["action"] == "create"
    applied = client.post("/venue-imports/apply", json={"preview_token": preview.json()["preview_token"]})
    assert applied.status_code == 201
    assert applied.json()["related_counts"]["created"] == 1
    venue = client.get("/venues?q=Venue With Contact").json()[0]
    assert client.get(f"/venues/{venue['id']}/contacts").json()[0]["email"] == "batch@example.com"

    exported = client.get("/venue-imports/export/contacts.csv")
    assert exported.status_code == 200
    assert "CON-BATCH-1" in exported.text


def test_document_upload_validates_content_and_downloads_safely():
    venue = client.post("/venues", json=venue_payload("VEN-NL-DR-ASSEN-UPLOAD", "Upload Venue")).json()
    pdf = b"%PDF-1.4\n%%EOF\n"
    uploaded = client.post(
        f"/venues/{venue['id']}/documents/upload",
        data={"document_external_id": "DOC-UPLOAD-1", "document_type": "site_map", "title": "Site map"},
        files={"file": ("map.pdf", pdf, "application/pdf")},
    )
    assert uploaded.status_code == 201
    document = uploaded.json()
    assert document["sha256"]
    downloaded = client.get(f"/venues/{venue['id']}/documents/{document['id']}/download")
    assert downloaded.status_code == 200
    assert downloaded.content == pdf

    rejected = client.post(
        f"/venues/{venue['id']}/documents/upload",
        data={"document_external_id": "DOC-UPLOAD-2", "document_type": "site_map", "title": "Fake"},
        files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
    )
    assert rejected.status_code == 415
