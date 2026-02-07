# Campus Pulse: Web-Based Campus Event & Participation Analytics System

Campus Pulse is a centralized platform designed to streamline event management, student registrations, and gate-entry analytics for college fests.

## 🚀 Key Features
**Admin Dashboard: An administrative dashboard for real-time event tracking and statistics.**

**Secure QR Authentication: Unique QR codes generated for every registration to ensure valid entry.**

**Digital Ticket System: Automated generation of digital passes with student and event details.**

**Glassmorphism UI: A high-end, dark-academic aesthetic across all student and admin portals.**

**Role-Based Access: Separate interfaces and permissions for students and Master Admins.** 

## 🛠️ Tech Stack

Backend: FastAPI (Python)

Database: SQLAlchemy with SQLite

Frontend: Jinja2 Templates, CSS3 (Glassmorphism), Vanilla JavaScript

Authentication: JWT (JSON Web Tokens) with HTTP-only Cookies

Tools: QR Code generation library, Pillow

## ⚙️ Setup & Installation

1. Clone the Repository
Bash
git clone https://github.com/YourUsername/campus-pulse.git
cd campus-pulse
2. Create a Virtual Environment
Bash
python -m venv venv
- Windows:
venv\Scripts\activate
- Mac/Linux:
source venv/bin/activate
3. Install Dependencies
Bash
pip install -r requirements.txt
4. Initialize the Database & Admin
Run the superuser script to create the database tables and the initial admin account:

Bash
python superuser.py
Default Admin Credentials:

Email: admin@campus.com
Password: campus_pulse

5. Run the Application
Bash
uvicorn app.main:app --reload
Access the application at: http://127.0.0.1:8000

## 📁 Project Structure

campus_pulse/
├── app/
│   ├── auth.py          # JWT & Hashing Logic
│   ├── database.py      # SQLAlchemy Configuration
│   ├── main.py          # FastAPI Core & Routes
│   ├── models/          # Database Models (User, Event, Registration)
│   ├── routers/         # Modular Auth & Event APIs
│   ├── static/          # CSS, JS, and Media Assets
│   └── templates/       # HTML Jinja2 Templates
├── requirements.txt     # Dependency List
└── superuser.py         # Admin Initialization Script

## 📝 License
Distributed under the MIT License. See LICENSE for more information.