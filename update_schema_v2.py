from app.config.database import SessionLocal, engine
from sqlalchemy import text

def update_schema():
    print("Updating schema...")
    with engine.connect() as conn:
        try:
            # 1. Add 'dni' to students
            print("Adding 'dni' to students...")
            try:
                conn.execute(text("ALTER TABLE students ADD COLUMN dni VARCHAR;"))
                # Create Unique Index for DNI if possible, but SQLite ALTER TABLE is limited.
                # simpler to just add column first. Unique constraint might need table recreation in SQLite 
                # but let's try to add unique index separately if needed or just rely on app logic for now/postgres.
                # If Postgres:
                # conn.execute(text("CREATE UNIQUE INDEX ix_students_dni ON students (dni);"))
                print("Added 'dni'.")
            except Exception as e:
                print(f"Skipping 'dni' (maybe exists): {e}")

        
            # 2. Add 'status' to attendance_logs
            print("Adding 'status' to attendance_logs...")
            try:
                conn.execute(text("ALTER TABLE attendance_logs ADD COLUMN status VARCHAR DEFAULT 'PRESENT';"))
                print("Added 'status'.")
            except Exception as e:
                print(f"Skipping 'status' (maybe exists): {e}")

            conn.commit()
            print("Schema update complete.")
        except Exception as e:
            print(f"General Error: {e}")

if __name__ == "__main__":
    update_schema()
