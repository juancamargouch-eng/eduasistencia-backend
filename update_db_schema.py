from app.config.database import SessionLocal, engine
from sqlalchemy import text

def add_column():
    db = SessionLocal()
    try:
        # Add event_type column to attendance_logs
        print("Adding event_type column to attendance_logs table...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE attendance_logs ADD COLUMN IF NOT EXISTS event_type VARCHAR DEFAULT 'ENTRY';"))
            conn.commit()
        print("Column added successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_column()
