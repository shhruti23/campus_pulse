from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    mobile_number = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)

    # Relationship to registrations
    registrations = relationship("Registration", back_populates="student")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    category = Column(String)
    location = Column(String)
    date_time = Column(DateTime)
    image_url = Column(String, default="/static/default.jpg")
    max_participants = Column(Integer, default=0)
    current_registrations = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Relationship to registrations
    registrations = relationship("Registration", back_populates="event")

class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    participation_type = Column(String) # Solo, Duo, Group
    participation_category = Column(String) # Dance, Song, etc.
    team_name = Column(String, nullable=True)
    team_members = Column(String, nullable=True)
    scan_count = Column(Integer, default=0)

    # Link back to User and Event
    student = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")