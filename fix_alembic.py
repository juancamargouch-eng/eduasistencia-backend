from app.config.database import SessionLocal
from sqlalchemy import text

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Revert alembic_version to the previous valid state 93aa462961fe
        db.execute(text("UPDATE alembic_version SET version_num='93aa462961fe'"))
        db.commit()
        print("alembic_version fixed.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()
