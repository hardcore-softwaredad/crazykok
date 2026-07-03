import os

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import models
from .database import Base, engine, get_db
from .schemas import EventCreate, EventRead, EventUpdate, OrganizerRead, VenueRead

app = FastAPI(title="Crazy Kok", version="0.1.0")


def cors_allowed_origins() -> list[str]:
    configured_origins = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "https://app.localhost",
    )
    return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_sqlite_event_columns() -> None:
    if not engine.url.get_backend_name().startswith("sqlite"):
        return

    columns = {
        "application_deadline": "DATE",
        "application_status": "VARCHAR(50) NOT NULL DEFAULT 'researching'",
        "source_url": "VARCHAR(500)",
        "notes": "TEXT",
    }

    with engine.begin() as connection:
        existing_columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(events)")).fetchall()
        }
        for column_name, column_type in columns.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE events ADD COLUMN {column_name} {column_type}"))


Base.metadata.create_all(bind=engine)
ensure_sqlite_event_columns()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/events", response_model=list[EventRead])
def list_events(
    q: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None, max_length=50),
    category: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=255),
    active: bool | None = Query(default=True),
    db: Session = Depends(get_db),
):
    query = db.query(models.Event)
    if q:
        search = f"%{q}%"
        query = query.filter(
            models.Event.name.ilike(search)
            | models.Event.location.ilike(search)
            | models.Event.organizer.ilike(search)
            | models.Event.category.ilike(search)
            | models.Event.notes.ilike(search)
        )
    if status:
        query = query.filter(models.Event.application_status == status)
    if category:
        query = query.filter(models.Event.category == category)
    if location:
        query = query.filter(models.Event.location.ilike(f"%{location}%"))
    if active is not None:
        query = query.filter(models.Event.is_active == active)
    return query.order_by(models.Event.event_date.asc().nulls_last()).all()


@app.post("/events", response_model=EventRead, status_code=201)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = models.Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@app.get("/events/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.patch("/events/{event_id}", response_model=EventRead)
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
def archive_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.is_active = False
    db.commit()
    db.refresh(event)
    return event


@app.post("/events/{event_id}/restore", response_model=EventRead)
def restore_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.is_active = True
    db.commit()
    db.refresh(event)
    return event


@app.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    db.delete(event)
    db.commit()


@app.get("/organizers", response_model=list[OrganizerRead])
def list_organizers(db: Session = Depends(get_db)):
    return db.query(models.Organizer).all()


@app.get("/venues", response_model=list[VenueRead])
def list_venues(db: Session = Depends(get_db)):
    return db.query(models.Venue).all()
