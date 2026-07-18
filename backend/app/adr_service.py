from __future__ import annotations

import fcntl
import hashlib
import os
import re
import tempfile
import threading
from contextlib import contextmanager
from datetime import date as Date
from pathlib import Path
from typing import Any, Iterator

import yaml
from pydantic import BaseModel, Field, field_validator


SCHEMA_VERSION = 1
STATUSES = ("proposed", "accepted", "rejected", "deprecated", "superseded")
STATUS_TRANSITIONS = {
    "proposed": set(STATUSES),
    "accepted": {"accepted", "deprecated", "superseded"},
    "rejected": {"rejected"},
    "deprecated": {"deprecated", "superseded"},
    "superseded": {"superseded"},
}
CATEGORIES = (
    "architecture",
    "backend",
    "data",
    "deployment",
    "domain",
    "frontend",
    "process",
    "product",
    "security",
)
REQUIRED_SECTIONS = (
    "Context",
    "Decision",
    "Consequences",
    "Alternatives Considered",
    "Review Trigger",
)
OPTIONAL_SECTIONS = ("Resources",)
METADATA_KEYS = {
    "schema_version",
    "id",
    "slug",
    "title",
    "status",
    "date",
    "category",
    "tags",
    "keywords",
    "supersedes",
    "superseded_by",
}
TOKEN_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ID_RE = re.compile(r"^\d{4}$")
FILE_RE = re.compile(r"^(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
HEADING_RE = re.compile(r"^# ADR (\d{4}): (.+)$", re.MULTILINE)
SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)
RAW_HTML_RE = re.compile(r"<\/?[A-Za-z][^>]*>")
PLACEHOLDER_RE = re.compile(r"^(?:\.\.\.|todo|tbd|placeholder)\.?$", re.IGNORECASE)
_thread_lock = threading.Lock()


class AdrError(Exception):
    def __init__(self, code: str, message: str, field: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field

    def payload(self) -> dict[str, str]:
        result = {"code": self.code, "message": self.message}
        if self.field:
            result["field"] = self.field
        return result


class AdrProposal(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    status: str = "proposed"
    date: Date = Field(default_factory=Date.today)
    category: str
    tags: list[str] = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    sections: dict[str, str]

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        return " ".join(value.split())


class AdrUpdateProposal(AdrProposal):
    expected_hash: str = Field(min_length=64, max_length=64)
    change_summary: str = Field(min_length=5, max_length=500)


class AdrRecord(BaseModel):
    schema_version: int
    id: str
    slug: str
    title: str
    status: str
    date: Date
    category: str
    tags: list[str]
    keywords: list[str]
    supersedes: list[str]
    superseded_by: list[str]
    sections: dict[str, str]
    markdown: str
    source_path: str
    content_hash: str


def slugify(title: str) -> str:
    value = title.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if not value:
        raise AdrError("invalid_slug", "Title does not produce a usable slug", "title")
    return value


def _normalise_values(values: list[str], field: str, tokens: bool) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = raw.strip().lower()
        key = value.casefold()
        if not value or key in seen:
            continue
        if tokens and not TOKEN_RE.fullmatch(value):
            raise AdrError("invalid_token", f"{field} values must use lower-case kebab-case", field)
        seen.add(key)
        cleaned.append(value)
    return sorted(cleaned, key=str.casefold)


def _validate_proposal(proposal: AdrProposal) -> AdrProposal:
    if proposal.status not in STATUSES:
        raise AdrError("invalid_status", f"Status must be one of: {', '.join(STATUSES)}", "status")
    if proposal.category not in CATEGORIES:
        raise AdrError("invalid_category", f"Category must be one of: {', '.join(CATEGORIES)}", "category")
    proposal.tags = _normalise_values(proposal.tags, "tags", True)
    proposal.keywords = _normalise_values(proposal.keywords, "keywords", False)
    if not proposal.tags:
        raise AdrError("missing_tags", "At least one tag is required", "tags")
    known_sections = set(REQUIRED_SECTIONS) | set(OPTIONAL_SECTIONS)
    if not set(REQUIRED_SECTIONS).issubset(proposal.sections) or not set(proposal.sections).issubset(known_sections):
        missing = sorted(set(REQUIRED_SECTIONS) - set(proposal.sections))
        extra = sorted(set(proposal.sections) - known_sections)
        detail = []
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        if extra:
            detail.append(f"unknown {', '.join(extra)}")
        raise AdrError("invalid_sections", "; ".join(detail), "sections")
    for heading, content in proposal.sections.items():
        value = content.strip()
        if not value or PLACEHOLDER_RE.fullmatch(value):
            raise AdrError("empty_section", f"{heading} must contain meaningful text", f"sections.{heading}")
        if RAW_HTML_RE.search(value):
            raise AdrError("raw_html", f"Raw HTML is not allowed in {heading}", f"sections.{heading}")
        proposal.sections[heading] = value
    for relation in proposal.supersedes:
        if not ID_RE.fullmatch(relation):
            raise AdrError("invalid_relation", "Related ADR IDs must contain four digits", "supersedes")
    proposal.supersedes = sorted(set(proposal.supersedes))
    return proposal


def _split_document(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        raise AdrError("missing_front_matter", "ADR must start with YAML front matter")
    try:
        _, raw_metadata, body = content.split("---\n", 2)
        metadata = yaml.safe_load(raw_metadata)
    except (ValueError, yaml.YAMLError) as error:
        raise AdrError("invalid_front_matter", f"Cannot parse YAML front matter: {error}") from error
    if not isinstance(metadata, dict):
        raise AdrError("invalid_front_matter", "YAML front matter must be a mapping")
    unknown = set(metadata) - METADATA_KEYS
    if unknown:
        raise AdrError("unknown_metadata", f"Unknown metadata: {', '.join(sorted(unknown))}")
    return metadata, body


def _parse_sections(body: str) -> tuple[str, str, dict[str, str]]:
    heading = HEADING_RE.search(body)
    if not heading:
        raise AdrError("invalid_heading", "ADR must have a canonical H1 heading")
    matches = list(SECTION_RE.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        if name in sections:
            raise AdrError("duplicate_heading", f"Duplicate section heading: {name}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[name] = body[match.end():end].strip()
    return heading.group(1), heading.group(2).strip(), sections


def parse_adr(path: Path) -> AdrRecord:
    if path.is_symlink():
        raise AdrError("symlink_rejected", f"ADR may not be a symlink: {path.name}")
    filename = FILE_RE.fullmatch(path.name)
    if not filename:
        raise AdrError("invalid_filename", f"Invalid ADR filename: {path.name}")
    content = path.read_text(encoding="utf-8")
    metadata, body = _split_document(content)
    heading_id, heading_title, sections = _parse_sections(body)
    required = METADATA_KEYS - {"supersedes", "superseded_by"}
    missing = required - set(metadata)
    if missing:
        raise AdrError("missing_metadata", f"Missing metadata: {', '.join(sorted(missing))}")
    record_id = str(metadata["id"])
    slug = str(metadata["slug"])
    title = str(metadata["title"])
    if not (record_id == filename.group(1) == heading_id):
        raise AdrError("id_mismatch", f"IDs disagree in {path.name}")
    if slug != filename.group(2):
        raise AdrError("slug_mismatch", f"Slug disagrees in {path.name}")
    if title != heading_title:
        raise AdrError("title_mismatch", f"Title disagrees in {path.name}")
    if metadata["schema_version"] != SCHEMA_VERSION:
        raise AdrError("unsupported_schema", f"Unsupported schema version in {path.name}")
    try:
        proposal = AdrProposal(
            title=title,
            status=metadata["status"],
            date=metadata["date"],
            category=metadata["category"],
            tags=metadata["tags"],
            keywords=metadata["keywords"],
            supersedes=metadata.get("supersedes", []),
            sections=sections,
        )
    except Exception as error:
        raise AdrError("invalid_metadata", str(error)) from error
    proposal = _validate_proposal(proposal)
    return AdrRecord(
        schema_version=int(metadata["schema_version"]),
        id=record_id,
        slug=slug,
        title=proposal.title,
        status=proposal.status,
        date=proposal.date,
        category=proposal.category,
        tags=proposal.tags,
        keywords=proposal.keywords,
        supersedes=proposal.supersedes,
        superseded_by=list(metadata.get("superseded_by", [])),
        sections=proposal.sections,
        markdown=body.strip() + "\n",
        source_path=str(path),
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )


def serialise_adr(record_id: str, slug: str, proposal: AdrProposal, superseded_by: list[str] | None = None) -> str:
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "id": record_id,
        "slug": slug,
        "title": proposal.title,
        "status": proposal.status,
        "date": proposal.date.isoformat(),
        "category": proposal.category,
        "tags": proposal.tags,
        "keywords": proposal.keywords,
        "supersedes": proposal.supersedes,
        "superseded_by": superseded_by or [],
    }
    front_matter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).strip()
    parts = [f"---\n{front_matter}\n---", f"# ADR {record_id}: {proposal.title}"]
    for heading in REQUIRED_SECTIONS:
        parts.append(f"## {heading}\n\n{proposal.sections[heading]}")
    for heading in OPTIONAL_SECTIONS:
        if heading in proposal.sections:
            parts.append(f"## {heading}\n\n{proposal.sections[heading]}")
    return "\n\n".join(parts) + "\n"


class AdrService:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def locked(self) -> Iterator[None]:
        lock_path = Path(tempfile.gettempdir()) / f"crazykok-adr-{hashlib.sha256(str(self.directory).encode()).hexdigest()[:12]}.lock"
        with _thread_lock, lock_path.open("w") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def list(self) -> list[AdrRecord]:
        records = [parse_adr(path) for path in sorted(self.directory.glob("*.md"))]
        ids = [record.id for record in records]
        slugs = [record.slug for record in records]
        if len(ids) != len(set(ids)):
            raise AdrError("duplicate_id", "ADR IDs must be unique")
        if len(slugs) != len(set(slugs)):
            raise AdrError("duplicate_slug", "ADR slugs must be unique")
        known = set(ids)
        for record in records:
            missing = set(record.supersedes) - known
            if missing:
                raise AdrError("missing_relation", f"{record.id} references missing ADRs: {', '.join(sorted(missing))}")
            if record.id in record.supersedes:
                raise AdrError("self_relation", f"{record.id} cannot supersede itself")
        graph = {record.id: record.supersedes for record in records}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(record_id: str) -> None:
            if record_id in visiting:
                raise AdrError("relationship_cycle", f"Supersession cycle includes ADR {record_id}")
            if record_id in visited:
                return
            visiting.add(record_id)
            for related_id in graph[record_id]:
                visit(related_id)
            visiting.remove(record_id)
            visited.add(record_id)

        for record_id in graph:
            visit(record_id)
        return sorted(records, key=lambda record: record.id)

    def get(self, record_id: str) -> AdrRecord:
        for record in self.list():
            if record.id == record_id:
                return record
        raise AdrError("not_found", f"ADR {record_id} was not found")

    def validate(self, proposal: AdrProposal, record_id: str = "0000", slug: str | None = None) -> dict[str, Any]:
        proposal = _validate_proposal(proposal)
        canonical_slug = slug or slugify(proposal.title)
        for relation in proposal.supersedes:
            self.get(relation)
        markdown = serialise_adr(record_id, canonical_slug, proposal)
        return {"valid": True, "warnings": [], "markdown": markdown, "slug": canonical_slug}

    def create(self, proposal: AdrProposal) -> AdrRecord:
        with self.locked():
            records = self.list()
            next_number = max((int(record.id) for record in records), default=0) + 1
            record_id = f"{next_number:04d}"
            slug = slugify(proposal.title)
            if any(record.slug == slug for record in records):
                raise AdrError("duplicate_slug", f"An ADR already uses slug {slug}", "title")
            self.validate(proposal, record_id, slug)
            path = self.directory / f"{record_id}-{slug}.md"
            content = serialise_adr(record_id, slug, proposal)
            self._atomic_write(path, content, create_only=True)
            return parse_adr(path)

    def update(self, record_id: str, proposal: AdrUpdateProposal) -> AdrRecord:
        with self.locked():
            current = self.get(record_id)
            proposal = _validate_proposal(proposal)
            if current.content_hash != proposal.expected_hash:
                raise AdrError("stale_source", "ADR changed after it was read; inspect it again before updating")
            if proposal.date != current.date:
                raise AdrError("immutable_field", "The original date is immutable", "date")
            if proposal.status not in STATUS_TRANSITIONS[current.status]:
                raise AdrError("invalid_status_transition", f"Cannot change status from {current.status} to {proposal.status}", "status")
            if current.status in {"accepted", "deprecated", "superseded"} and proposal.sections["Decision"].strip() != current.sections["Decision"].strip():
                raise AdrError("new_adr_required", "Material decisions must be changed by a superseding ADR", "sections.Decision")
            self.validate(proposal, record_id, current.slug)
            path = Path(current.source_path)
            content = serialise_adr(record_id, current.slug, proposal, current.superseded_by)
            self._atomic_write(path, content)
            return parse_adr(path)

    @staticmethod
    def _atomic_write(path: Path, content: str, create_only: bool = False) -> None:
        if path.exists() and path.is_symlink():
            raise AdrError("symlink_rejected", "Refusing to replace a symlink")
        if create_only and path.exists():
            raise AdrError("duplicate_id", f"ADR file already exists: {path.name}")
        descriptor, temporary = tempfile.mkstemp(prefix=".adr-", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
