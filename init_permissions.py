from app.config.database import SessionLocal
from app.models.module_permission import ModulePermission

def init_permissions():
    db = SessionLocal()
    try:
        # Check if already initialized
        if db.query(ModulePermission).count() > 0:
            print("Los permisos ya están inicializados.")
            return

        # Default permissions map matching current static implementation
        default_map = {
            'ADMIN': [
                'dashboard', 'registration', 'students', 'daily_attendance', 
                'occupancy', 'tasks', 'announcements', 'reports', 
                'justifications', 'telegram', 'settings', 'users' # Super Admin sees users
            ],
            'DIRECTOR': [
                'dashboard', 'registration', 'students', 'daily_attendance', 
                'occupancy', 'tasks', 'announcements', 'reports', 
                'justifications', 'telegram', 'settings'
            ],
            'DOCENTE': [
                'dashboard', 'students', 'daily_attendance', 
                'occupancy', 'tasks', 'announcements', 'justifications'
            ],
        }

        all_modules = [
            'dashboard', 'registration', 'students', 'daily_attendance', 
            'occupancy', 'tasks', 'announcements', 'reports', 
            'justifications', 'telegram', 'settings', 'users'
        ]

        for role, enabled_modules in default_map.items():
            for module in all_modules:
                is_enabled = module in enabled_modules
                p = ModulePermission(role=role, module_name=module, is_enabled=is_enabled)
                db.add(p)
        
        db.commit()
        print("Matriz de permisos inicializada con éxito.")
    except Exception as e:
        print(f"Error inicializando permisos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_permissions()
