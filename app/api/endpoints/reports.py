from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import StreamingResponse
from ...config.database import get_db
from ...models.attendance import AttendanceLog
from ...models.student import Student
import pandas as pd
import io
from datetime import date

from ...api import deps
from ...models.user import User

router = APIRouter()

@router.get("/attendance/export")
def export_attendance(
    from_date: date,
    to_date: date,
    grade: str = None,
    section: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    try:
        # Robustly handle empty or 'undefined' values from frontend
        def clean_filter(value):
            if not value or str(value).strip().lower() in ["", "undefined", "null", "none", "todos", "todas"]:
                return None
            return value.strip()

        grade = clean_filter(grade)
        section = clean_filter(section)
        
        print(f"DEBUG: EXPORT REQUEST - From: {from_date}, To: {to_date}, Grade: {grade}, Section: {section}")
        
        # Date Filtering using robust casting to Date
        from sqlalchemy import Date, cast
        
        query = db.query(AttendanceLog).join(Student).options(
            joinedload(AttendanceLog.student).joinedload(Student.schedule)
        )
        
        # Filter by date only (ignoring time/timezone for comparison)
        query = query.filter(cast(AttendanceLog.timestamp, Date) >= from_date)
        query = query.filter(cast(AttendanceLog.timestamp, Date) <= to_date)
        
        if grade:
            query = query.filter(Student.grade == grade)
        if section:
            query = query.filter(Student.section == section)

        logs = query.all()
        print(f"DEBUG: FINAL QUERY RESULT - Logs found: {len(logs)}")

        if not logs:
            print("DEBUG: No logs found, generating empty Excel.")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                pd.DataFrame(columns=["Sin Datos"]).to_excel(writer, index=False, sheet_name='Sin Datos')
            output.seek(0)
            headers = {'Content-Disposition': f'attachment; filename="asistencia_{from_date}_{to_date}.xlsx"'}
            return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # 1. Get all students matching filters
        student_query = db.query(Student).options(joinedload(Student.schedule))
        if grade:
            student_query = student_query.filter(Student.grade == grade)
        if section:
            student_query = student_query.filter(Student.section == section)
        
        students = student_query.all()
        print(f"DEBUG: Students to report: {len(students)}")

        # 2. Get all logs in range
        log_query = db.query(AttendanceLog).join(Student)
        log_query = log_query.filter(cast(AttendanceLog.timestamp, Date) >= from_date)
        log_query = log_query.filter(cast(AttendanceLog.timestamp, Date) <= to_date)
        
        if grade:
            log_query = log_query.filter(Student.grade == grade)
        if section:
            log_query = log_query.filter(Student.section == section)
            
        logs = log_query.all()
        print(f"DEBUG: Logs found in range: {len(logs)}")

        # 3. Create a mapping (student_id, date) -> log
        from collections import defaultdict
        attendance_map = defaultdict(lambda: None)
        for log in logs:
            # We prioritize successful logs for the report
            key = (log.student_id, log.timestamp.date())
            existing = attendance_map[key]
            if not existing or (not existing.verification_status and log.verification_status):
                attendance_map[key] = log

        # 4. Generate Date Range
        import datetime
        date_range = []
        curr = from_date
        while curr <= to_date:
            date_range.append(curr)
            curr += datetime.timedelta(days=1)

        # 5. Build Final Data
        data = []
        for student in students:
            for d in date_range:
                log = attendance_map[(student.id, d)]
                
                status = "Falta"
                hora = ""
                tipo = "Entrada"
                
                if log:
                    tipo = "Entrada" if log.event_type == "ENTRY" else "Salida"
                    hora = log.timestamp.strftime("%H:%M:%S")
                    if log.verification_status:
                        status = "Tardanza" if log.status == "LATE" else "Presente"
                    else:
                        status = f"Intento Fallido ({log.failure_reason or 'Error'})"

                data.append({
                    "ID": student.id,
                    "DNI": student.dni,
                    "Nombre": student.full_name,
                    "Grado": student.grade,
                    "Sección": student.section,
                    "Fecha": d.strftime("%Y-%m-%d"),
                    "Hora": hora,
                    "Turno": student.schedule.name if student.schedule else "N/A",
                    "Estado": status,
                    "Tipo": tipo
                })

        df_all = pd.DataFrame(data)
        
        output = io.BytesIO()
        print(f"DEBUG: Writing Excel with {len(df_all)} rows (Matrix style)")
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if df_all.empty:
                pd.DataFrame(columns=["Sin Datos"]).to_excel(writer, index=False, sheet_name='Reporte')
            else:
                unique_grades = sorted(df_all['Grado'].unique())
                for g in unique_grades:
                    df_grade = df_all[df_all['Grado'] == g].copy()
                    df_grade = df_grade.sort_values(by=['Fecha', 'Sección', 'Nombre'])
                    sheet_name = str(g)[:30].replace("/", "-")
                    df_grade.to_excel(writer, index=False, sheet_name=sheet_name)
                    
                    worksheet = writer.sheets[sheet_name]
                    for column_cells in worksheet.columns:
                        items = [str(cell.value) for cell in column_cells if cell.value is not None]
                        if items:
                            length = max(len(i) for i in items)
                            worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)
        
        output.seek(0)
        
        headers = {
            'Content-Disposition': f'attachment; filename="asistencia_{from_date}_{to_date}.xlsx"'
        }
        
        return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
