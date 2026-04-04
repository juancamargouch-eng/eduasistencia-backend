from app.config.database import SessionLocal
from app.models.user import User

def fix_user_roles():
    db = SessionLocal()
    try:
        users_without_role = db.query(User).filter(User.role == None).all()
        print(f"Encontrados {len(users_without_role)} usuarios sin rol.")
        
        for user in users_without_role:
            if user.is_superuser:
                user.role = "ADMIN"
            else:
                user.role = "DOCENTE"
            print(f"Actualizando usuario {user.username} a rol: {user.role}")
        
        db.commit()
        print("Actualización completada con éxito.")
    except Exception as e:
        print(f"Error actualizando roles: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_user_roles()
