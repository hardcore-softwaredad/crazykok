from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal, engine, get_db
from .schemas import EventCreate, EventRead, OrganizerRead, VenueRead

app = FastAPI(title="Crazy Kok Venues", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/events", response_model=list[EventRead])
def list_events(
    q: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Event)
    if q:
        query = query.filter(models.Event.name.ilike(f"%{q}%"))
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


@app.get("/organizers", response_model=list[OrganizerRead])
def list_organizers(db: Session = Depends(get_db)):
    return db.query(models.Organizer).all()


@app.get("/venues", response_model=list[VenueRead])
def list_venues(db: Session = Depends(get_db)):
    return db.query(models.Venue).all()
