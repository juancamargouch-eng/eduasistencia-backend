from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..config.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500), nullable=True)

    # Relaciones
    assignments = relationship("TeacherAssignment", back_populates="course")


class AcademicPeriod(Base):
    __tablename__ = "academic_periods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # e.g. "I Bimestre"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relaciones
    grades = relationship("Grade", back_populates="period")


class EvaluationCriteria(Base):
    __tablename__ = "evaluation_criteria"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False) # e.g. "Actitud"
    weight_percentage = Column(Integer, default=0, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relaciones
    grades = relationship("Grade", back_populates="criterion")


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    grade = Column(String(50), nullable=False) # e.g. "3ro"
    section = Column(String(50), nullable=False) # e.g. "A"

    # Relaciones
    user = relationship("User")
    course = relationship("Course", back_populates="assignments")
    grades = relationship("Grade", back_populates="assignment")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("teacher_assignments.id", ondelete="CASCADE"), nullable=False)
    criterion_id = Column(Integer, ForeignKey("evaluation_criteria.id", ondelete="CASCADE"), nullable=False)
    period_id = Column(Integer, ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False)
    score_value = Column(String(10), nullable=False) # "15", "18.5", "AD", "B"
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relaciones
    student = relationship("Student")
    assignment = relationship("TeacherAssignment", back_populates="grades")
    criterion = relationship("EvaluationCriteria", back_populates="grades")
    period = relationship("AcademicPeriod", back_populates="grades")


class AcademicSetting(Base):
    __tablename__ = "academic_settings"

    id = Column(Integer, primary_key=True, index=True)
    # "NUMERIC" (0-20, 0-10) o "LITERAL" (AD, A, B, C)
    grading_system = Column(String(20), default="NUMERIC", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
