"""Add string length limits and check constraints

Revision ID: cecff12a800e
Revises: 3ab3ac8c54e7
Create Date: 2026-03-06 02:02:45.921087

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cecff12a800e'
down_revision: Union[str, None] = '3ab3ac8c54e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Estudiantes
    op.alter_column('students', 'full_name', type_=sa.String(255))
    op.alter_column('students', 'grade', type_=sa.String(50))
    op.alter_column('students', 'section', type_=sa.String(10))
    op.alter_column('students', 'dni', type_=sa.String(20))
    op.alter_column('students', 'qr_code_hash', type_=sa.String(100))
    op.alter_column('students', 'photo_url', type_=sa.String(512))
    op.alter_column('students', 'telegram_chat_id', type_=sa.String(50))
    op.alter_column('students', 'telegram_user_id', type_=sa.String(50))

    # Logs de Asistencia
    op.alter_column('attendance_logs', 'failure_reason', type_=sa.String(255))
    op.alter_column('attendance_logs', 'event_type', type_=sa.String(20))
    op.alter_column('attendance_logs', 'status', type_=sa.String(20))
    op.create_check_constraint('ck_attendance_confidence', 'attendance_logs', 'confidence_score >= 0 AND confidence_score <= 1')

    # Usuarios
    op.alter_column('users', 'username', type_=sa.String(50))
    op.alter_column('users', 'hashed_password', type_=sa.String(255))
    op.alter_column('users', 'email', type_=sa.String(255))

    # Dispositivos
    op.alter_column('devices', 'name', type_=sa.String(100))
    op.alter_column('devices', 'ip_address', type_=sa.String(45))
    op.alter_column('devices', 'location', type_=sa.String(255))
    op.alter_column('devices', 'device_type', type_=sa.String(50))

    # Justificaciones
    op.alter_column('justifications', 'reason', type_=sa.String(500))
    op.alter_column('justifications', 'status', type_=sa.String(20))
    op.alter_column('justifications', 'evidence_url', type_=sa.String(512))

    # Horarios
    op.alter_column('schedules', 'slug', type_=sa.String(50))
    op.alter_column('schedules', 'name', type_=sa.String(100))
    op.create_check_constraint('ck_schedule_tolerance', 'schedules', 'tolerance_minutes >= 0')
    op.create_check_constraint('ck_schedule_late_limit', 'schedules', 'late_limit_minutes >= 0')


def downgrade() -> None:
    """Downgrade schema."""
    # Horarios
    op.drop_constraint('ck_schedule_late_limit', 'schedules')
    op.drop_constraint('ck_schedule_tolerance', 'schedules')
    op.alter_column('schedules', 'name', type_=sa.String())
    op.alter_column('schedules', 'slug', type_=sa.String())

    # Justificaciones
    op.alter_column('justifications', 'evidence_url', type_=sa.String())
    op.alter_column('justifications', 'status', type_=sa.String())
    op.alter_column('justifications', 'reason', type_=sa.String())

    # Dispositivos
    op.alter_column('devices', 'device_type', type_=sa.String())
    op.alter_column('devices', 'location', type_=sa.String())
    op.alter_column('devices', 'ip_address', type_=sa.String())
    op.alter_column('devices', 'name', type_=sa.String())

    # Usuarios
    op.alter_column('users', 'email', type_=sa.String())
    op.alter_column('users', 'hashed_password', type_=sa.String())
    op.alter_column('users', 'username', type_=sa.String())

    # Logs de Asistencia
    op.drop_constraint('ck_attendance_confidence', 'attendance_logs')
    op.alter_column('attendance_logs', 'status', type_=sa.String())
    op.alter_column('attendance_logs', 'event_type', type_=sa.String())
    op.alter_column('attendance_logs', 'failure_reason', type_=sa.String())

    # Estudiantes
    op.alter_column('students', 'telegram_user_id', type_=sa.String())
    op.alter_column('students', 'telegram_chat_id', type_=sa.String())
    op.alter_column('students', 'photo_url', type_=sa.String())
    op.alter_column('students', 'qr_code_hash', type_=sa.String())
    op.alter_column('students', 'dni', type_=sa.String())
    op.alter_column('students', 'section', type_=sa.String())
    op.alter_column('students', 'grade', type_=sa.String())
    op.alter_column('students', 'full_name', type_=sa.String())
