from datetime import date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from backend.app.adr_service import AdrError, AdrProposal, AdrService, AdrUpdateProposal
from backend.app.main import app


def proposal(**overrides):
    values = {
        "title": "Use Files For Decisions",
        "status": "proposed",
        "date": date(2026, 7, 3),
        "category": "architecture",
        "tags": ["documentation", "adr", "adr"],
        "keywords": ["decision record"],
        "supersedes": [],
        "sections": {
            "Context": "Decisions need durable context.",
            "Decision": "Keep decisions as repository files.",
            "Consequences": "Git records every reviewed change.",
            "Alternatives Considered": "Store decisions in a database.",
            "Review Trigger": "Review when concurrent remote authors are needed.",
        },
    }
    values.update(overrides)
    return AdrProposal(**values)


def test_create_allocates_ids_and_writes_canonical_files(tmp_path: Path):
    service = AdrService(tmp_path)
    first = service.create(proposal())
    second = service.create(proposal(title="Validate Decision Files"))

    assert first.id == "0001"
    assert second.id == "0002"
    assert first.tags == ["adr", "documentation"]
    assert (tmp_path / "0001-use-files-for-decisions.md").exists()
    assert service.get("0001").content_hash == first.content_hash


def test_invalid_proposal_does_not_write(tmp_path: Path):
    service = AdrService(tmp_path)
    invalid = proposal(tags=["Not Valid"])

    with pytest.raises(AdrError, match="kebab-case"):
        service.create(invalid)

    assert list(tmp_path.iterdir()) == []


def test_update_requires_current_hash_and_preserves_identity(tmp_path: Path):
    service = AdrService(tmp_path)
    created = service.create(proposal())
    values = proposal().model_dump()
    values.update(expected_hash="0" * 64, change_summary="Clarify the consequences")

    with pytest.raises(AdrError) as error:
        service.update(created.id, AdrUpdateProposal(**values))
    assert error.value.code == "stale_source"

    values["expected_hash"] = created.content_hash
    values["status"] = "accepted"
    updated = service.update(created.id, AdrUpdateProposal(**values))
    assert updated.id == created.id
    assert updated.slug == created.slug
    assert updated.status == "accepted"


def test_resources_are_an_optional_preserved_section(tmp_path: Path):
    record = AdrService(tmp_path).create(proposal(sections=dict(proposal().sections, Resources="- [Diagram](assets/diagram.svg)")))

    assert record.sections["Resources"] == "- [Diagram](assets/diagram.svg)"
    assert "## Resources\n\n- [Diagram](assets/diagram.svg)" in record.markdown


def test_accepted_decision_cannot_be_rewritten(tmp_path: Path):
    service = AdrService(tmp_path)
    accepted = service.create(proposal(status="accepted"))
    values = proposal(status="accepted").model_dump()
    values["sections"] = dict(values["sections"], Decision="Replace the historical decision.")
    values.update(expected_hash=accepted.content_hash, change_summary="Rewrite it")

    with pytest.raises(AdrError) as error:
        service.update(accepted.id, AdrUpdateProposal(**values))
    assert error.value.code == "new_adr_required"


def test_concurrent_creation_allocates_unique_ids(tmp_path: Path):
    service = AdrService(tmp_path)

    def create(index: int):
        return service.create(proposal(title=f"Concurrent Decision {index}"))

    with ThreadPoolExecutor(max_workers=4) as executor:
        records = list(executor.map(create, range(1, 9)))

    assert sorted(record.id for record in records) == [f"{number:04d}" for number in range(1, 9)]
    assert len(list(tmp_path.glob("*.md"))) == 8


def test_raw_html_and_path_like_titles_are_safe(tmp_path: Path):
    service = AdrService(tmp_path)
    unsafe_sections = dict(proposal().sections)
    unsafe_sections["Context"] = "<script>alert('no')</script>"
    with pytest.raises(AdrError) as error:
        service.create(proposal(sections=unsafe_sections))
    assert error.value.code == "raw_html"

    record = service.create(proposal(title="../../A Safe Decision"))
    assert record.slug == "a-safe-decision"
    assert Path(record.source_path).parent == tmp_path.resolve()


def test_repository_adrs_follow_the_contract():
    repository = Path(__file__).resolve().parents[2]
    records = AdrService(repository / "docs" / "adr").list()
    assert len(records) >= 27
    assert len({record.id for record in records}) == len(records)


def test_internal_routes_are_disabled_outside_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ADR_AUTHORING_ENABLED", "false")
    response = TestClient(app).get("/internal/adrs/schema")
    assert response.status_code == 404


def test_internal_create_returns_docs_url(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ADR_AUTHORING_ENABLED", "true")
    monkeypatch.setenv("ADR_DIRECTORY", str(tmp_path))
    monkeypatch.setenv("DOCS_ORIGIN", "https://docs.example.test")
    payload = proposal().model_dump(mode="json")

    response = TestClient(app).post("/internal/adrs", json=payload)

    assert response.status_code == 201
    assert response.json()["id"] == "0001"
    assert response.json()["docs_url"] == "https://docs.example.test/adr/use-files-for-decisions"
