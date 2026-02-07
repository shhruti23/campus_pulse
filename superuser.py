# File: superuser.py
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine 
from app.models import models
from passlib.context import CryptContext

# --- CONFIGURATION (Sync with Master Admin credentials) ---
ADMIN_EMAIL = "shrutisharma2308@gmail.com"
ADMIN_PASSWORD = "gungun" 
ADMIN_NAME = "Master Admin"
# ---------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_super_user():
    db = SessionLocal()
    try:
        # 1. Verification of existing identity
        existing_user = db.query(models.User).filter(models.User.email == ADMIN_EMAIL).first()
        if existing_user:
            print(f"⚠️ IDENTITY ALREADY REGISTERED: {ADMIN_EMAIL}")
            return

        # 2. Cryptographic hashing
        print(f"Initialising secure hash for {ADMIN_EMAIL}...")
        hashed_pw = pwd_context.hash(ADMIN_PASSWORD)

        # 3. Provisioning the Superuser record
        db_user = models.User(
            email=ADMIN_EMAIL,
            hashed_password=hashed_pw, 
            full_name=ADMIN_NAME,
            is_admin=True, 
            is_blocked=False,
            mobile_number="0000000000", # Placeholder for admin account
            branch="ADMINISTRATION"
        )

        db.add(db_user)
        db.commit()
        print(f"✅ SYSTEM READY: Superuser deployed successfully: {ADMIN_EMAIL}")

    except Exception as e:
        print(f"❌ DEPLOYMENT FAILURE: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure tables exist before provisioning
    models.Base.metadata.create_all(bind=engine)
    create_super_user()