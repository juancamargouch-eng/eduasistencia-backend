import sys
import os

# Add the current directory to sys.path to allow imports from app
sys.path.append(os.getcwd())

try:
    from app.services.attendance_service import AttendanceService
    from app.services.student_service import StudentService
    print("SUCCESS: Imports are working fine.")
except Exception as e:
    import traceback
    print("ERROR: Import failed!")
    traceback.print_exc()
