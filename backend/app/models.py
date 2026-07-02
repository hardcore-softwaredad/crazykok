from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    event_date = Column(Date, nullable=True)
    organizer = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    expected_revenue = Column(Integer, nullable=True)
    expected_attendance = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class Organizer(Base):
    __tablename__ = "organizers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    contact_email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    capacity = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
