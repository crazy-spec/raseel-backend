"""
Create the Raseel super admin account.
Run once: python create_admin.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
os.environ["USE_SQLITE"] = "true"

from app.database import create_tables, SessionLocal
from app.models.user import User, UserRole
from app.auth.utils import hash_password

# === EDIT THESE ===
ADMIN_EMAIL = "admin@raseel.sa"
ADMIN_PASSWORD = "Raseel2026!"
ADMIN_NAME = "Raseel Admin"
ADMIN_PHONE = "+966553431867"
# ==================

def main():
    print("")
    print("=" * 50)
    print("  RASEEL - Create Super Admin")
    print("=" * 50)

    # Make sure tables exist (creates users table)
    create_tables()

    db = SessionLocal()
    try:
        # Check if already exists
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing:
            print("")
            print("  Admin already exists: " + existing.email)
            print("  Role: " + existing.role)
            print("  ID: " + existing.id)
            print("")
            print("  To reset password, delete and re-run.")
            return

        # Create admin
        admin = User(
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            full_name=ADMIN_NAME,
            phone=ADMIN_PHONE,
            role=UserRole.SUPER_ADMIN.value,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("")
        print("  Super Admin Created!")
        print("  -----------------------")
        print("  Email:    " + ADMIN_EMAIL)
        print("  Password: " + ADMIN_PASSWORD)
        print("  Role:     super_admin")
        print("  ID:       " + admin.id)
        print("")
        print("  SAVE THESE CREDENTIALS!")
        print("=" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    main()
