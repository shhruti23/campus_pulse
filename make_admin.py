from app.database import SessionLocal
from app.models import models

def set_admin(email):
    db = SessionLocal()
    try:
        # Querying the Pulse user database
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if user:
            # Granting administrative authorization
            user.is_admin = True
            db.commit()
            print(f"✓ ACCESS GRANTED: {email} is now an Authorized Admin for Campus Pulse.")
        else:
            print("❌ SIGNAL NOT FOUND: This email has not been registered in the system.")
            print("Please sign up via the browser first.")
            
    except Exception as e:
        db.rollback()
        print(f"⚠️ SYSTEM ERROR: Could not promote user. Details: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("--- CAMPUS PULSE: ADMINISTRATIVE ELEVATION UTILITY ---")
    email_to_promote = input("Enter the registered student email: ").strip()
    
    if email_to_promote:
        set_admin(email_to_promote)
    else:
        print("Invalid input. Execution terminated.")