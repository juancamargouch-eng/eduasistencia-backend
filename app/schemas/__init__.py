from .student import Student, StudentCreate, StudentBase, StudentUpdate, StudentKiosk, StudentPagination
from .attendance import AttendanceLog, AttendanceLogCreate, AttendanceLogBase, AttendanceLogKiosk, AttendancePagination, DailyAttendancePagination, OccupancyPagination, AttendancePercentage
from .user import User, UserCreate, UserBase, Token, TokenData
from .telegram import TelegramConfig, TelegramConfigCreate, TelegramConfigBase, TelegramCodeRequest, TelegramLoginRequest
from .assignment import Assignment, AssignmentCreate, AssignmentUpdate
from .announcement import Announcement, AnnouncementCreate, AnnouncementUpdate
from .module_permission import ModulePermission, ModulePermissionBase
from .academic import (
    CourseBase, CourseCreate, CourseUpdate, CourseResponse,
    AcademicPeriodBase, AcademicPeriodCreate, AcademicPeriodUpdate, AcademicPeriodResponse,
    EvaluationCriteriaBase, EvaluationCriteriaCreate, EvaluationCriteriaUpdate, EvaluationCriteriaResponse,
    TeacherAssignmentBase, TeacherAssignmentCreate, TeacherAssignmentUpdate, TeacherAssignmentResponse,
    GradeBase, GradeCreate, GradeResponse, BulkGradeUpload,
    AcademicSettingBase, AcademicSettingCreate, AcademicSettingUpdate, AcademicSettingResponse
)
