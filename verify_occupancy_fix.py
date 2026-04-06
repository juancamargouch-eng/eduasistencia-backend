import sys
import os
import json
from datetime import date

# Add current dir to path
sys.path.append(os.getcwd())

try:
    from app.services.attendance_service import AttendanceService
    from app.config.database import SessionLocal
    from app import models

    db = SessionLocal()
    
    print("Testing SIMULATED Occupancy Stats flow...")
    # Call the newly restored method
    stats = AttendanceService.get_occupancy_stats(db, skip=0, limit=5)
    
    print("SUCCESS: Occupancy stats are working perfectly!")
    print(f"Current Count: {stats['current_count']}")
    print(f"Total Entries Today: {stats['total_entries']}")
    print(f"Total Exits Today: {stats['total_exits']}")
    print(f"Items in list: {len(stats['items'])}")

except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    if 'db' in locals():
        db.close()
