from datetime import date

# Feriados Nacionales de Perú (MVP 2024-2026)
# Formato: (mes, dia)
HOLIDAYS_PE = {
    (1, 1): "Año Nuevo",
    (3, 28): "Jueves Santo", # Variable, aproximado MVP
    (3, 29): "Viernes Santo", # Variable, aproximado MVP
    (5, 1): "Día del Trabajo",
    (6, 7): "Batalla de Arica y Día de la Bandera",
    (6, 29): "San Pedro y San Pablo",
    (7, 23): "Día de la Fuerza Aérea",
    (7, 28): "Fiestas Patrias",
    (7, 29): "Fiestas Patrias",
    (8, 6): "Batalla de Junín",
    (8, 30): "Santa Rosa de Lima",
    (10, 8): "Combate de Angamos",
    (11, 1): "Día de Todos los Santos",
    (12, 8): "Inmaculada Concepción",
    (12, 9): "Batalla de Ayacucho",
    (12, 25): "Navidad"
}

def get_holiday_name(check_date: date) -> str | None:
    """Retorna el nombre del feriado si la fecha lo es, de lo contrario None."""
    return HOLIDAYS_PE.get((check_date.month, check_date.day))

def is_weekend(check_date: date) -> bool:
    """Retorna True si la fecha cae Sábado (5) o Domingo (6)."""
    return check_date.weekday() >= 5

def is_non_working_day(check_date: date) -> bool:
    """Retorna True si es feriado o fin de semana."""
    return is_weekend(check_date) or get_holiday_name(check_date) is not None
