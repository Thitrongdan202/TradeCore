import os
import secrets
import string
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def seed_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("Admin user already exists.")
            return

        password = os.getenv("ADMIN_PASSWORD")
        if not password:
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(secrets.choice(alphabet) for i in range(16))
            print(f"\n[WARNING] ADMIN_PASSWORD not found in environment. Generating secure random password.")

        admin = User(
            username="admin",
            email="admin@tradecore.vn",
            full_name="Quản Trị Viên",
            hashed_password=get_password_hash(password),
            is_active=True
        )
        db.add(admin)
        db.commit()
        print(f"\n==========================================")
        print(f"Admin user created successfully")
        print(f"Username: admin")
        print(f"Password: {password}")
        print(f"==========================================\n")
    except Exception as e:
        print(f"Error seeding admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
