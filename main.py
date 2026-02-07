import os
import shutil
import datetime
from typing import List
from io import BytesIO

from fastapi import FastAPI, Request, Depends, Form, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from jose import jwt, JWTError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
import qrcode

# 1. IMPORTS
from app.database import engine, get_db
# Pulling models directly to avoid AttributeError
from app.models import Base, User, Event, Registration 
from app.routers import auth_routes, event_routes
from app.auth import SECRET_KEY, ALGORITHM

# 2. CREATE TABLES
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Campus Pulse")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# 3. ROUTERS
app.include_router(auth_routes.router)
app.include_router(event_routes.router)

# --- HELPER: GET USER ---
def get_current_user(request: Request, db: Session):
    token = request.cookies.get("access_token")
    if not token: return None
    if token.startswith("Bearer "): token = token[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id") # Must match what you put in the token
        return db.query(User).filter(User.id == user_id).first()
    except (JWTError, AttributeError):
        return None

# --- ERROR HANDLER ---
@app.exception_handler(StarletteHTTPException)
async def custom_404(request, exc):
    if exc.status_code == 404: 
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


# ==========================
#      WEBSITE ROUTES
# ==========================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request): 
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request): 
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    # Redirect admin to their specific portal
    if user.is_admin: return RedirectResponse(url="/admin")
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/event-details", response_class=HTMLResponse)
async def event_details_page(request: Request): 
    return templates.TemplateResponse("event_details.html", {"request": request})

# --- PROFILE COMPLETION ---
@app.get("/complete-profile", response_class=HTMLResponse)
async def complete_profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    if user.mobile_number and user.branch: return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("register_details.html", {"request": request, "user": user})

@app.post("/complete-profile")
async def save_profile(request: Request, mobile_number: str = Form(...), branch: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        user.mobile_number = mobile_number
        user.branch = branch
        db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

# --- NEW EVENT REGISTRATION ---
@app.get("/register-event/{event_id}", response_class=HTMLResponse)
async def show_event_registration_form(event_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    
    if not user.mobile_number or not user.branch:
        return RedirectResponse(url="/complete-profile")
        
    event = db.query(Event).filter(Event.id == event_id).first()
    return templates.TemplateResponse("event_register.html", {"request": request, "user": user, "event": event})

@app.post("/register-event/{event_id}")
async def process_event_registration(
    event_id: int, request: Request,
    participation_type: str = Form(...),
    participation_category: str = Form(...),
    team_name: str = Form(None),
    team_members: str = Form(None),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")

    existing = db.query(Registration).filter(
        Registration.user_id == user.id, 
        Registration.event_id == event_id
    ).first()

    if existing:
        return templates.TemplateResponse("event_register.html", {
            "request": request, "user": user, "event": existing.event, "error": "Already Secure!"
        })

    new_reg = Registration(
        user_id=user.id,
        event_id=event_id,
        participation_type=participation_type,
        participation_category=participation_category,
        team_name=team_name,
        team_members=team_members,
        scan_count=0 
    )
    db.add(new_reg)
    db.commit()

    return RedirectResponse(url="/dashboard?success=1", status_code=302)

# ===============================
#      ADMIN & API ROUTES
# ===============================

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not user.is_admin: return RedirectResponse(url="/login")
    events = db.query(Event).all()
    return templates.TemplateResponse("admin.html", {"request": request, "events": events})

@app.get("/admin/event/{event_id}/users", response_class=HTMLResponse)
async def view_event_users(event_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not user.is_admin: return RedirectResponse(url="/login")

    event = db.query(Event).filter(Event.id == event_id).first()
    registrations = db.query(Registration).filter(Registration.event_id == event_id).all()
    
    return templates.TemplateResponse("event_users.html", {
        "request": request, "event": event, "registrations": registrations
    })

# --- QR & TICKETS ---

@app.get("/ticket/{event_id}", response_class=HTMLResponse)
async def generate_ticket(event_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    
    reg = db.query(Registration).filter(
        Registration.user_id == user.id, 
        Registration.event_id == event_id
    ).first()
    
    if not reg: return HTMLResponse("<h1>Void: Registration Not Found</h1>")
    event = db.query(Event).filter(Event.id == event_id).first()
    return templates.TemplateResponse("ticket.html", {"request": request, "user": user, "event": event, "reg_id": f"CP-{event.id}-{user.id}"})

@app.get("/generate-qr/{ticket_id}")
async def generate_qr_code(ticket_id: str):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(ticket_id)
    qr.make(fit=True)
    # High contrast white background for better scanning
    img = qr.make_image(fill_color="#710014", back_color="white") 
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

# --- ADMIN SCANNER ---

class TicketScan(BaseModel):
    ticket_id: str

@app.get("/scanner", response_class=HTMLResponse)
async def scanner_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("scanner.html", {"request": request})

# POST Route for QR validation
@app.post("/events/scan-ticket")
async def scan_ticket(scan: TicketScan, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        return JSONResponse(status_code=403, content={"message": "ADMIN PRIVILEGE REQUIRED"})

    try:
        parts = scan.ticket_id.split("-")
        event_id, user_id = int(parts[1]), int(parts[2])
    except:
        return JSONResponse(status_code=400, content={"message": "MALFORMED TICKET"})

    reg = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.user_id == user_id
    ).first()

    if not reg: return JSONResponse(status_code=404, content={"message": "ENTRY NOT FOUND"})

    reg.scan_count += 1
    db.commit()
    
    msg = "VERIFIED" if reg.scan_count == 1 else f"RE-ENTRY DETECTED ({reg.scan_count})"
    return {"status": "success", "message": f"{msg}: {reg.student.full_name}", "scan_count": reg.scan_count}