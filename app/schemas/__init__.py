from .student import Student, StudentCreate, StudentBase, StudentUpdate, StudentKiosk, StudentPagination
from .attendance import AttendanceLog, AttendanceLogCreate, AttendanceLogBase, AttendanceLogKiosk, AttendancePagination, DailyAttendancePagination, OccupancyPagination, AttendancePercentage
from .user import User, UserCreate, UserBase, Token, TokenData
from .telegram import TelegramConfig, TelegramConfigCreate, TelegramConfigBase, TelegramCodeRequest, TelegramLoginRequest
from .assignment import Assignment, AssignmentCreate, AssignmentUpdate
from .announcement import Announcement, AnnouncementCreate, AnnouncementUpdate
from .module_permission import ModulePermission, ModulePermissionBase
