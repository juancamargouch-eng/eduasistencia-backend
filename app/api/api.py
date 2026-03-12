from fastapi import APIRouter
from .endpoints import auth, students, attendance, schedules, justifications, reports, devices, settings, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(justifications.router, prefix="/justifications", tags=["justifications"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
