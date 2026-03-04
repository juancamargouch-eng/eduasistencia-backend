import os
from dotenv import load_dotenv

# Load environment variables at the very beginning
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config.database import engine, Base
from .api.api import api_router
from app.core.websocket_manager import manager

# Import models to ensure they are registered with Base
from .models import * 

# Create tables on startup (good for MVP, use migrations for prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Asistencia Escolar Inteligente")

# CORS middleware
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
origins = [origin.strip() for origin in cors_origins_str.split(",")]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# Ensure static directory exists
STATIC_DIR = "static/students"
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

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
