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

    # Mejor lógica: Solo crear el administrador inicial si NO existe NINGÚN superusuario en el sistema.
    # Esto permite que el usuario cambie su nombre de usuario o contraseña sin que el seeder
    # intente recrear la cuenta original cada vez que se reinicia el servidor.
    any_superuser = db.query(User).filter(User.is_superuser == True).first()
    
    if not any_superuser:
        print(f"No se encontró ningún administrador. Creando usuario inicial: {admin_user}...")
        new_admin = User(
            username=admin_user,
            full_name="Administrador Inicial",
            email="admin@school.com",
            hashed_password=get_password_hash(admin_password),
            is_superuser=True,
            is_active=True
        )
        db.add(new_admin)
        db.commit()
        print(f"Usuario {admin_user} creado exitosamente como administrador inicial.")
    else:
        print(f"El sistema ya cuenta con al menos un administrador ('{any_superuser.username}'). Saltando seeding.")
    
    db.close()

if __name__ == "__main__":
    seed()
