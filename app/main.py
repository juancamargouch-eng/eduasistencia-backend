import os
from dotenv import load_dotenv

# Load environment variables at the very beginning
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config.database import engine, Base
from .api.api import api_router
from app.core.websocket_manager import manager
from app.core.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


# Import models to ensure they are registered with Base
from .models import * 

def run_migrations_and_seed():
    try:
        # MIGRACIONES AUTOMÁTICAS: Sincroniza la base de datos profesionalmente al iniciar
        from alembic.config import Config
        from alembic import command
        from seeder import seed  # Importar el seeder

        print("Revisando y aplicando migraciones de base de datos...")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Base de datos sincronizada correctamente.")
        
        # Ejecutar el seeder para asegurar el usuario administrador inicial
        print("Ejecutando seeder para usuario administrador...")
        seed()
    except ImportError:
        print("AVISO: El módulo 'alembic' no está instalado. Saltando migraciones automáticas.")
    except Exception as e:
        print(f"Error en el proceso de inicio de base de datos: {e}")

# Ejecutar procesos de base de datos antes de iniciar la app
run_migrations_and_seed()

app = FastAPI(title="Sistema de Asistencia Escolar Inteligente")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - Configuración dinámica
cors_origins_str = os.getenv("CORS_ORIGINS", "")
# Dominios locales por defecto para desarrollo
default_origins = ["http://localhost:5173", "http://localhost:3000"]

# Unificar y filtrar duplicados: .env + locales
env_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
origins = list(set(default_origins + env_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount removed as we use S3 Proxy
# app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"DEBUG VALIDATION ERROR: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

app.include_router(api_router, prefix="/api")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {"message": "Welcome to School Attendance System API"}
