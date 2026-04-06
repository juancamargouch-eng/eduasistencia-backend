from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List

from app import models, schemas
from app.api import deps
from app.models.user import User

router = APIRouter()

# ----------------- PERIODOS ACADÉMICOS -----------------
@router.get("/periods/", response_model=List[schemas.AcademicPeriodResponse])
def get_periods(db: Session = Depends(deps.get_db)):
    """Trae todos los periodos académicos (Admin & Docs)."""
    return db.query(models.AcademicPeriod).all()

@router.post("/periods/", response_model=schemas.AcademicPeriodResponse)
def create_period(period: schemas.AcademicPeriodCreate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    """Crea un nuevo periodo (Admin)."""
    db_period = models.AcademicPeriod(**period.model_dump())
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return db_period

@router.put("/periods/{period_id}", response_model=schemas.AcademicPeriodResponse)
def update_period(period_id: int, period_in: schemas.AcademicPeriodUpdate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    """Edita un periodo académico (Admin)."""
    db_period = db.query(models.AcademicPeriod).filter(models.AcademicPeriod.id == period_id).first()
    if not db_period:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
    
    update_data = period_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_period, field, value)
    
    db.commit()
    db.refresh(db_period)
    return db_period

@router.delete("/periods/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_period(period_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    """Elimina un periodo académico (Admin). Solo si no tiene notas."""
    db_period = db.query(models.AcademicPeriod).filter(models.AcademicPeriod.id == period_id).first()
    if not db_period:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
    
    # Validación de Integridad
    if db_period.grades:
        raise HTTPException(status_code=400, detail="No se puede eliminar un periodo que ya tiene notas registradas. Primero debe eliminar las notas vinculadas.")
    
    db.delete(db_period)
    db.commit()
    return None

# ----------------- CURSOS (MALLA) -----------------
@router.get("/courses/", response_model=List[schemas.CourseResponse])
def get_courses(db: Session = Depends(deps.get_db)):
    return db.query(models.Course).all()

@router.post("/courses/", response_model=schemas.CourseResponse)
def create_course(course: schemas.CourseCreate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.put("/courses/{course_id}", response_model=schemas.CourseResponse)
def update_course(course_id: int, course_in: schemas.CourseUpdate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    """Edita un curso de la malla (Admin)."""
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    update_data = course_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_course, field, value)
    
    db.commit()
    db.refresh(db_course)
    return db_course

@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    """Elimina un curso (Admin). Solo si no tiene docentes asignados."""
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Validación de Integridad
    if db_course.assignments:
        raise HTTPException(status_code=400, detail="No se puede eliminar un curso que tiene docentes asignados. Primero debe eliminar las asignaciones de carga horaria.")
    
    db.delete(db_course)
    db.commit()
    return None

# ----------------- CRITERIOS -----------------
@router.get("/criteria/", response_model=List[schemas.EvaluationCriteriaResponse])
def get_criteria(db: Session = Depends(deps.get_db)):
    return db.query(models.EvaluationCriteria).all()

@router.post("/criteria/", response_model=schemas.EvaluationCriteriaResponse)
def create_criteria(criteria: schemas.EvaluationCriteriaCreate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    db_criteria = models.EvaluationCriteria(**criteria.model_dump())
    db.add(db_criteria)
    db.commit()
    db.refresh(db_criteria)
    return db_criteria

@router.put("/criteria/{criteria_id}", response_model=schemas.EvaluationCriteriaResponse)
def update_criteria(criteria_id: int, criteria_in: schemas.EvaluationCriteriaUpdate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    """Edita un rubro/criterio de evaluación (Admin)."""
    db_criteria = db.query(models.EvaluationCriteria).filter(models.EvaluationCriteria.id == criteria_id).first()
    if not db_criteria:
        raise HTTPException(status_code=404, detail="Criterio no encontrado")
    
    update_data = criteria_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_criteria, field, value)
    
    db.commit()
    db.refresh(db_criteria)
    return db_criteria

@router.delete("/criteria/{criteria_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_criteria(criteria_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    """Elimina un rubro (Admin). Solo si no tiene notas vinculadas."""
    db_criteria = db.query(models.EvaluationCriteria).filter(models.EvaluationCriteria.id == criteria_id).first()
    if not db_criteria:
        raise HTTPException(status_code=404, detail="Criterio no encontrado")
    
    # Validación de Integridad
    if db_criteria.grades:
        raise HTTPException(status_code=400, detail="No se puede eliminar un criterio que ya tiene notas registradas.")
    
    db.delete(db_criteria)
    db.commit()
    return None

# ----------------- ASIGNACIONES GLOBALES (ADMIN) -----------------
@router.get("/assignments/", response_model=List[schemas.TeacherAssignmentResponse])
def get_all_assignments(db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    return db.query(models.TeacherAssignment).all()

@router.post("/assignments/", response_model=schemas.TeacherAssignmentResponse)
def create_assignment(assignment: schemas.TeacherAssignmentCreate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    db_assign = models.TeacherAssignment(**assignment.model_dump())
    db.add(db_assign)
    db.commit()
    db.refresh(db_assign)
    return db_assign

@router.put("/assignments/{assignment_id}", response_model=schemas.TeacherAssignmentResponse)
def update_assignment(assignment_id: int, assignment_in: schemas.TeacherAssignmentUpdate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    """Edita una asignación docente (Admin)."""
    db_assign = db.query(models.TeacherAssignment).filter(models.TeacherAssignment.id == assignment_id).first()
    if not db_assign:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    update_data = assignment_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_assign, field, value)
    
    db.commit()
    db.refresh(db_assign)
    return db_assign

@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    """Elimina una carga académica (Admin). Solo si no tiene notas cargadas por el docente."""
    db_assign = db.query(models.TeacherAssignment).filter(models.TeacherAssignment.id == assignment_id).first()
    if not db_assign:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    # Validación de Integridad
    if db_assign.grades:
        raise HTTPException(status_code=400, detail="No se puede eliminar una asignación que ya tiene notas registradas.")
    
    db.delete(db_assign)
    db.commit()
    return None

# ----------------- FLUJO DEL DOCENTE -----------------
@router.get("/teacher/my-assignments")
def get_my_assignments(db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    """Obtiene exclusivamente la carga académica del docente logueado con datos enriquecidos (nombre del curso)."""
    assignments_db = db.query(models.TeacherAssignment).options(
        joinedload(models.TeacherAssignment.course)
    ).filter(models.TeacherAssignment.user_id == current_user.id).all()
    
    # Custom response to include course name without breaking simple schemas
    result = []
    for ass in assignments_db:
        result.append({
            "id": ass.id,
            "user_id": ass.user_id,
            "course_id": ass.course_id,
            "course_name": ass.course.name if ass.course else "Curso Desconocido",
            "grade": ass.grade,
            "section": ass.section
        })
    return result

@router.post("/teacher/bulk-grades")
def bulk_upload_grades(payload: schemas.BulkGradeUpload, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    """Permite enviar una lista de notas. Si la nota ya existe (idéntico estudiante, asignación, periodo y criterio), la sobrescribe (Upsert)."""
    upserted_count = 0
    for grade_data in payload.grades:
        # Check ownership (security)
        assignment = db.query(models.TeacherAssignment).filter(
            models.TeacherAssignment.id == grade_data.assignment_id,
            models.TeacherAssignment.user_id == current_user.id
        ).first()

        if not assignment and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="No tienes permisos sobre esta asignación académica.")

        # Find existing grade combination
        existing_grade = db.query(models.Grade).filter(
            models.Grade.student_id == grade_data.student_id,
            models.Grade.assignment_id == grade_data.assignment_id,
            models.Grade.criterion_id == grade_data.criterion_id,
            models.Grade.period_id == grade_data.period_id
        ).first()

        if existing_grade:
            existing_grade.score_value = grade_data.score_value
        else:
            new_grade = models.Grade(**grade_data.model_dump())
            db.add(new_grade)
        upserted_count += 1
        
    db.commit()
    return {"status": "success", "upserted_count": upserted_count}

@router.get("/teacher/grades")
def get_grades_for_assignment(assignment_id: int, period_id: int, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    """Obtiene todas las notas cargadas para un salón en un periodo, para renderizar la libreta."""
    assignment = db.query(models.TeacherAssignment).filter(models.TeacherAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Asignación no encontrada.")

    if assignment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Permiso denegado.")

    grades = db.query(models.Grade).filter(
        models.Grade.assignment_id == assignment_id,
        models.Grade.period_id == period_id
    ).all()

    return grades

# ----------------- CONFIGURACION GLOBAL -----------------
@router.get("/settings/", response_model=schemas.AcademicSettingResponse)
def get_settings(db: Session = Depends(deps.get_db)):
    setting = db.query(models.AcademicSetting).first()
    if not setting:
        setting = models.AcademicSetting(grading_system="NUMERIC")
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting

@router.put("/settings/", response_model=schemas.AcademicSettingResponse)
def update_settings(settings_update: schemas.AcademicSettingUpdate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_superuser)):
    setting = db.query(models.AcademicSetting).first()
    if not setting:
        setting = models.AcademicSetting(**settings_update.model_dump())
        db.add(setting)
    else:
        setting.grading_system = settings_update.grading_system
    
    db.commit()
    db.refresh(setting)
    return setting
