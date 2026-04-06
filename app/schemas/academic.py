from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

# Global Settings
class AcademicSettingBase(BaseModel):
    grading_system: str

class AcademicSettingCreate(AcademicSettingBase):
    pass

class AcademicSettingUpdate(AcademicSettingBase):
    pass

class AcademicSettingResponse(AcademicSettingBase):
    id: int
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Courses
class CourseBase(BaseModel):
    name: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(CourseBase):
    name: Optional[str] = None

class CourseResponse(CourseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# Academic Periods
class AcademicPeriodBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_active: bool = True

class AcademicPeriodCreate(AcademicPeriodBase):
    pass

class AcademicPeriodUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

class AcademicPeriodResponse(AcademicPeriodBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# Evaluation Criteria
class EvaluationCriteriaBase(BaseModel):
    name: str
    weight_percentage: Optional[int] = 0
    is_active: bool = True

class EvaluationCriteriaCreate(EvaluationCriteriaBase):
    pass

class EvaluationCriteriaUpdate(BaseModel):
    name: Optional[str] = None
    weight_percentage: Optional[int] = None
    is_active: Optional[bool] = None

class EvaluationCriteriaResponse(EvaluationCriteriaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# Teacher Assignments
class TeacherAssignmentBase(BaseModel):
    user_id: int
    course_id: int
    grade: Optional[str] = ""
    section: Optional[str] = ""

class TeacherAssignmentCreate(TeacherAssignmentBase):
    pass

class TeacherAssignmentUpdate(BaseModel):
    grade: Optional[str] = None
    section: Optional[str] = None

class TeacherAssignmentResponse(TeacherAssignmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# Grades
class GradeBase(BaseModel):
    student_id: int
    assignment_id: int
    criterion_id: int
    period_id: int
    score_value: Optional[str] = ""

class GradeCreate(GradeBase):
    pass

class GradeResponse(GradeBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class BulkGradeUpload(BaseModel):
    grades: List[GradeCreate]
