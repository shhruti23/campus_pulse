from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
# Direct imports to prevent AttributeError
from app.models import Event, Registration, User
from pydantic import BaseModel

router = APIRouter(prefix="/events", tags=["Events"])

# --- SCHEMAS ---
class TicketScan(BaseModel):
    ticket_id: str

# --- ROUTES ---

@router.get("/", response_model=List[dict])
def get_all_events(db: Session = Depends(get_db)):
    # Direct reference to Event model
    events = db.query(Event).filter(Event.is_active == True).all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "category": e.category,
            "location": e.location,
            "date_time": e.date_time,
            "image_url": e.image_url,
            "max_participants": e.max_participants,
            "current_registrations": e.current_registrations
        } for e in events
    ]

@router.get("/{event_id}")
def get_event_by_id(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event frequency not found")
    return event

@router.post("/scan-ticket")
def validate_ticket(scan: TicketScan, db: Session = Depends(get_db)):
    """
    Validates the QR code data sent from scanner.html
    """
    try:
        # Expected format: CP-EVENTID-USERID
        parts = scan.ticket_id.split("-")
        if len(parts) != 3 or parts[0] != "CP":
            raise ValueError()
        
        event_id = int(parts[1])
        user_id = int(parts[2])
    except:
        raise HTTPException(status_code=400, detail="INVALID SIGNAL: CORRUPT TICKET")

    registration = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.user_id == user_id
    ).first()

    if not registration:
        raise HTTPException(status_code=404, detail="ENTRY NOT FOUND IN MANIFEST")

    # Update Pulse Log
    registration.scan_count += 1
    db.commit()
    db.refresh(registration)

    status_prefix = "VERIFIED" if registration.scan_count == 1 else f"RE-ENTRY ({registration.scan_count})"
    
    return {
        "status": "success",
        "message": f"{status_prefix}: {registration.student.full_name}",
        "scan_count": registration.scan_count
    }