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
        print(f"DEBUG: Exporting for {from_date} to {to_date}, Grade: {grade}, Section: {section}")
        
        # Fix Date Filtering
        from datetime import datetime, time
        
        start_dt = datetime.combine(from_date, time.min)
        end_dt = datetime.combine(to_date, time.max)
        
        query = db.query(AttendanceLog).join(Student).options(joinedload(AttendanceLog.student).joinedload(Student.schedule))
        query = query.filter(AttendanceLog.timestamp >= start_dt)
        query = query.filter(AttendanceLog.timestamp <= end_dt)
        
        if grade:
            query = query.filter(Student.grade == grade)
        if section:
            print(f"DEBUG: Filtering by section: {section}")
            query = query.filter(Student.section == section)

        logs = query.all()
        print(f"DEBUG: Found {len(logs)} logs")

        if not logs:
             # Return empty excel if no logs
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                pd.DataFrame().to_excel(writer, sheet_name='Sin Datos')
            output.seek(0)
            headers = {'Content-Disposition': f'attachment; filename="asistencia_{from_date}_{to_date}.xlsx"'}
            return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # LOGIC REFINEMENT: Group by (Student, Date, EventType)
        # Prioritize SUCCESS over FAILURE
        from collections import defaultdict
        
        grouped_logs = defaultdict(list)
        
        for log in logs:
            if not log.student:
                continue
            # Key: (student_id, date, event_type)
            key = (log.student_id, log.timestamp.date(), log.event_type)
            grouped_logs[key].append(log)
            
        final_logs = []
        
        for key, group in grouped_logs.items():
            # Check if any success exists
            success_logs = [l for l in group if l.verification_status]
            
            if success_logs:
                # If success exists, add ALL success logs (usually just one)
                final_logs.extend(success_logs)
            else:
                # If no success, add ALL failed logs (so admin sees attempting)
                final_logs.extend(group)
                
        # Sort by timestamp to keep order
        final_logs.sort(key=lambda x: x.timestamp)

        # Prepare Data
        data = []
        for log in final_logs:
            # Determine mapped status
            display_status = "Ausente/Fallido"
            if log.verification_status:
                if log.status == "LATE":
                    display_status = "Tardanza"
                else:
                    display_status = "Presente"

            data.append({
                "ID": log.student_id,
                "DNI": log.student.dni,
                "Nombre": log.student.full_name,
                "Grado": log.student.grade,
                "Sección": log.student.section,
                "Fecha": log.timestamp.strftime("%Y-%m-%d") if log.timestamp else "",
                "Hora": log.timestamp.strftime("%H:%M:%S") if log.timestamp else "",
                "Turno": log.student.schedule.name if log.student.schedule else "N/A",
                "Estado": display_status,
                "Tipo": "Entrada" if log.event_type == "ENTRY" else "Salida"
            })

        df_all = pd.DataFrame(data)
        
        output = io.BytesIO()
        print("DEBUG: Writing Excel with Multiple Sheets")
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Get unique grades to create sheets
            # If a specific grade was filtered, only that one exists
            unique_grades = sorted(df_all['Grado'].unique())
            
            for g in unique_grades:
                # Filter by grade
                df_grade = df_all[df_all['Grado'] == g].copy()
                
                # Sort by Section and Name
                df_grade = df_grade.sort_values(by=['Sección', 'Nombre'])
                
                # Clean sheet name (remove invalid chars if any, limit length)
                sheet_name = str(g)[:30].replace("/", "-")
                
                df_grade.to_excel(writer, index=False, sheet_name=sheet_name)
                
                # Auto-adjust columns width (Basic attempt)
                worksheet = writer.sheets[sheet_name]
                for column_cells in worksheet.columns:
                    length = max(len(str(cell.value) or "") for cell in column_cells)
                    worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2
        
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
