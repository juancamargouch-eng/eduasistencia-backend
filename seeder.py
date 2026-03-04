from sqlalchemy.orm import Session
from app.config.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import get_password_hash
import sys

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    
    # Check if admin exists
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        print("Creating admin user...")
        admin_user = User(
            username="admin",
            email="admin@school.com",
            hashed_password=get_password_hash("admin123"), # Change in production
            is_superuser=True,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created: admin / admin123")
    else:
        print("Admin user already exists.")
    
    db.close()

if __name__ == "__main__":
    seed()
