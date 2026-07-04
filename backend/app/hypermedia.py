from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import ceil
from urllib.parse import urlencode, urlsplit, urlunsplit

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field


HAL_MEDIA_TYPE = "application/hal+json"
PROBLEM_MEDIA_TYPE = "application/problem+json"


class HALJSONResponse(JSONResponse):
    media_type = HAL_MEDIA_TYPE


class ProblemJSONResponse(JSONResponse):
    media_type = PROBLEM_MEDIA_TYPE


class HALLink(BaseModel):
    href: str
    templated: bool | None = None


class HALModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class PageMetadata(BaseModel):
    number: int
    size: int
    total_elements: int
    total_pages: int


class HALResource(HALModel):
    links: dict[str, HALLink | list[HALLink]] = Field(alias="_links")


class HALCollection(HALModel):
    links: dict[str, HALLink] = Field(alias="_links")
    page: PageMetadata


@dataclass(frozen=True)
class Page:
    number: int
    size: int
    total_elements: int

    @property
    def total_pages(self) -> int:
        return ceil(self.total_elements / self.size) if self.total_elements else 0

    def metadata(self) -> PageMetadata:
        return PageMetadata(
            number=self.number,
            size=self.size,
            total_elements=self.total_elements,
            total_pages=self.total_pages,
        )


def _trusted_proxy_headers() -> bool:
    configured = os.getenv("TRUST_PROXY_HEADERS")
    if configured is not None:
        return configured.lower() in {"1", "true", "yes", "on"}
    return os.getenv("APP_ENV", "development") != "production"


def _first_header_value(value: str | None) -> str | None:
    return value.split(",", 1)[0].strip() if value else None


def public_api_base(request: Request) -> str:
    configured = os.getenv("PUBLIC_API_BASE_URL")
    if configured:
        return configured.rstrip("/")

    scheme = request.url.scheme
    host = request.headers.get("host", request.url.netloc)
    prefix = ""
    if _trusted_proxy_headers():
        scheme = _first_header_value(request.headers.get("x-forwarded-proto")) or scheme
        host = _first_header_value(request.headers.get("x-forwarded-host")) or host
        prefix = _first_header_value(request.headers.get("x-forwarded-prefix")) or ""

    normalized_prefix = f"/{prefix.strip('/')}" if prefix.strip("/") else ""
    return f"{scheme}://{host}{normalized_prefix}/v1"


def api_url(
    request: Request,
    path: str = "",
    query: Sequence[tuple[str, str | int | bool]] | None = None,
) -> str:
    base = public_api_base(request)
    normalized_path = path.strip("/")
    url = f"{base}/{normalized_path}" if normalized_path else base
    if query:
        url = f"{url}?{_encode_query(query)}"
    return url


def _encode_query(query: Iterable[tuple[str, str | int | bool]]) -> str:
    return urlencode(
        [
            (key, str(value).lower() if isinstance(value, bool) else value)
            for key, value in query
        ]
    )


def replace_url_query(url: str, query: Iterable[tuple[str, str | int | bool]]) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, _encode_query(query), parts.fragment))


def pagination_links(
    request: Request,
    path: str,
    query: Sequence[tuple[str, str | int | bool]],
    page: Page,
) -> dict[str, HALLink]:
    without_page = [(key, value) for key, value in query if key != "page"]

    def page_url(number: int) -> str:
        return api_url(request, path, [*without_page, ("page", number)])

    links = {"self": HALLink(href=page_url(page.number))}
    if page.total_pages:
        links["first"] = HALLink(href=page_url(1))
        links["last"] = HALLink(href=page_url(page.total_pages))
        if page.number > 1:
            links["prev"] = HALLink(href=page_url(page.number - 1))
        if page.number < page.total_pages:
            links["next"] = HALLink(href=page_url(page.number + 1))
    return links
