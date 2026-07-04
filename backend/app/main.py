import os

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import models
from .adr_routes import router as adr_router
from .api_v1 import router as api_v1_router
from .database import get_db
from .hypermedia import ProblemJSONResponse, api_url
from .opportunity_service import filtered_opportunities, ordered_opportunities
from .schemas import EventCreate, EventRead, EventUpdate, OrganizerRead
from .venue_routes import import_router as venue_import_router
from .venue_routes import router as venue_router

app = FastAPI(title="Crazy Kok", version="0.1.0")
app.include_router(adr_router)
app.include_router(api_v1_router)
app.include_router(venue_router)
app.include_router(venue_import_router)


def cors_allowed_origins() -> list[str]:
    configured_origins = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "https://crazykok.local,https://app.crazykok.local",
    )
    return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def is_v1_path(path: str) -> bool:
    return path == "/v1" or path.startswith("/v1/")


def public_request_url(request: Request) -> str:
    path = request.url.path.removeprefix("/v1").strip("/")
    return api_url(request, path, list(request.query_params.multi_items()))


@app.middleware("http")
async def api_contract_headers(request: Request, call_next):
    response = await call_next(request)
    if is_v1_path(request.url.path):
        vary = response.headers.get("Vary")
        response.headers["Vary"] = f"{vary}, Accept" if vary else "Accept"
    elif request.url.path in {"/events", "/opportunities"} or request.url.path.startswith(("/events/", "/opportunities/")):
        response.headers["Deprecation"] = "true"
        response.headers["Link"] = '</v1/opportunities>; rel="successor-version"'
    return response


@app.exception_handler(HTTPException)
async def http_problem(request: Request, exc: HTTPException):
    if not is_v1_path(request.url.path):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": jsonable_encoder(exc.detail)},
            headers=exc.headers,
        )
    return ProblemJSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://crazykok.com/problems/http-{exc.status_code}",
            "title": "Request failed",
            "status": exc.status_code,
            "detail": str(exc.detail),
            "instance": public_request_url(request),
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_problem(request: Request, exc: RequestValidationError):
    errors = jsonable_encoder(exc.errors())
    if not is_v1_path(request.url.path):
        return JSONResponse(status_code=422, content={"detail": errors})
    return ProblemJSONResponse(
        status_code=422,
        content={
            "type": "https://crazykok.com/problems/validation-error",
            "title": "Request validation failed",
            "status": 422,
            "detail": "One or more request values are invalid.",
            "instance": public_request_url(request),
            "errors": errors,
        },
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/events", response_model=list[EventRead], deprecated=True)
@app.get("/opportunities", response_model=list[EventRead], deprecated=True)
def list_events(
    q: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None, max_length=50),
    category: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=255),
    active: bool | None = Query(default=True),
    db: Session = Depends(get_db),
):
    query = filtered_opportunities(
        db, q=q, status=status, category=category, location=location, active=active
    )
    return ordered_opportunities(query, "event_date", "asc").all()


@app.post("/events", response_model=EventRead, status_code=201, deprecated=True)
@app.post("/opportunities", response_model=EventRead, status_code=201, deprecated=True)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = models.Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@app.get("/events/{event_id}", response_model=EventRead)
@app.get("/opportunities/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.patch("/events/{event_id}", response_model=EventRead)
@app.patch("/opportunities/{event_id}", response_model=EventRead)
def update_event(event_id: int, event_update: EventUpdate, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for field, value in event_update.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return event


@app.post("/events/{event_id}/archive", response_model=EventRead)
@app.post("/opportunities/{event_id}/archive", response_model=EventRead)
def archive_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.is_active = False
    db.commit()
    db.refresh(event)
    return event


@app.post("/events/{event_id}/restore", response_model=EventRead)
@app.post("/opportunities/{event_id}/restore", response_model=EventRead)
def restore_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.is_active = True
    db.commit()
    db.refresh(event)
    return event


@app.delete("/events/{event_id}", status_code=204)
@app.delete("/opportunities/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    db.delete(event)
    db.commit()


@app.get("/organizers", response_model=list[OrganizerRead])
def list_organizers(db: Session = Depends(get_db)):
    return db.query(models.Organizer).all()
