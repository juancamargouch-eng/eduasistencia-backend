import sys
from dotenv import load_dotenv

sys.path.append(r'c:\Users\juanc\Desktop\sistema de asistencia\backend')
load_dotenv(r'c:\Users\juanc\Desktop\sistema de asistencia\backend\.env')

from app.config.database import SessionLocal
from app.services.attendance_service import AttendanceService

db = SessionLocal()
try:
    res = AttendanceService.get_attendance_percentages(db, 'month')
    print('MARCH_MONTH_SUMMARY:')
    print(res)
except Exception as e:
    print('ERROR:', e)
finally:
    db.close()
