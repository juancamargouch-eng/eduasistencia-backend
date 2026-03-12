from sqlalchemy.orm import Session
from app.config.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import get_password_hash
import sys

# El seeder ya no crea tablas, eso lo hace Alembic.
import os

def seed():
    db = SessionLocal()
    
    # Obtener credenciales estrictamente desde el entorno (.env)
    admin_user = os.getenv("FIRST_ADMIN_USER")
    admin_password = os.getenv("FIRST_ADMIN_PASSWORD")
    
    if not admin_user or not admin_password:
        print("ADVERTENCIA: No se han configurado FIRST_ADMIN_USER o FIRST_ADMIN_PASSWORD en el .env.")
        print("El seeder no creará ningún usuario administrativo por razones de seguridad.")
        db.close()
        return

    # Check if admin exists
    user = db.query(User).filter(User.username == admin_user).first()
    if not user:
        print(f"Creando usuario administrador: {admin_user}...")
        new_admin = User(
            username=admin_user,
            full_name="Administrador del Sistema",
            email="admin@school.com",
            hashed_password=get_password_hash(admin_password),
            is_superuser=True,
            is_active=True
        )
        db.add(new_admin)
        db.commit()
        print(f"Usuario {admin_user} creado exitosamente.")
    else:
        print(f"El usuario administrador '{admin_user}' ya existe.")
    
    db.close()

if __name__ == "__main__":
    seed()
