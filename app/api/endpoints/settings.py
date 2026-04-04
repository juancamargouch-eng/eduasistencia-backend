from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
from app.services.telegram_service import TelegramService

router = APIRouter()

@router.get("/telegram", response_model=schemas.TelegramConfig)
def get_telegram_config(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    config = db.query(models.TelegramConfig).first()
    if not config:
        config = models.TelegramConfig(bot_token="", api_id="", api_hash="", is_active=False)
        db.add(config)
        db.commit()
        db.refresh(config)
    
    # Creamos un objeto de respuesta con datos enmascarados para PROD
    def mask_value(val: str, prefix_len: int = 2) -> str:
        if not val or len(val) < 8: return val
        return f"{val[:prefix_len]}{'*' * (len(val) - prefix_len)}"

    response_config = schemas.TelegramConfig.from_orm(config)
    if config.bot_token: response_config.bot_token = mask_value(config.bot_token, 10)
    if config.api_id: response_config.api_id = mask_value(config.api_id, 2)
    if config.api_hash: response_config.api_hash = mask_value(config.api_hash, 4)
    
    return response_config

@router.post("/telegram", response_model=schemas.TelegramConfig)
def update_telegram_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: schemas.TelegramConfigCreate,
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    config = db.query(models.TelegramConfig).first()
    update_data = config_in.dict(exclude_unset=True)
    
    # Lógica de protección: No sobreescribir si vienen datos enmascarados (con asteriscos)
    clean_update = {}
    for field, value in update_data.items():
        if value and "*" in value:
            continue # Ignorar valores enmascarados que vienen del front
        clean_update[field] = value

    if not config:
        config = models.TelegramConfig(**clean_update)
        db.add(config)
    else:
        for field, value in clean_update.items():
            setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    # Retornar enmascarado también tras el update
    def mask_value(val: str, prefix_len: int = 2) -> str:
        if not val or len(val) < 8: return val
        return f"{val[:prefix_len]}{'*' * (len(val) - prefix_len)}"

    response_config = schemas.TelegramConfig.from_orm(config)
    if config.bot_token: response_config.bot_token = mask_value(config.bot_token, 10)
    if config.api_id: response_config.api_id = mask_value(config.api_id, 2)
    if config.api_hash: response_config.api_hash = mask_value(config.api_hash, 4)
    
    return response_config

@router.post("/telegram/send-code")
async def send_telegram_code(
    *,
    db: Session = Depends(deps.get_db),
    request: schemas.TelegramCodeRequest,
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    config = db.query(models.TelegramConfig).first()
    if not config or not config.api_id or not config.api_hash:
        raise HTTPException(status_code=400, detail="API ID y API Hash son requeridos primero")
    
    try:
        phone_code_hash = await TelegramService.send_code_request(
            config.api_id, config.api_hash, request.phone
        )
        return {"phone_code_hash": phone_code_hash}
    except Exception as e:
        print(f"Error en send_telegram_code: {str(e)}")
        # If it's a known Telethon error, we try to be more specific
        error_msg = str(e)
        if "API_ID_INVALID" in error_msg:
            error_msg = "El API ID o API Hash proporcionados son inválidos."
        elif "PHONE_NUMBER_INVALID" in error_msg:
            error_msg = "El número de teléfono ingresado no es válido."
            
        raise HTTPException(status_code=400, detail=error_msg)

@router.post("/telegram/login")
async def login_telegram_user(
    *,
    db: Session = Depends(deps.get_db),
    request: schemas.TelegramLoginRequest,
    current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    config = db.query(models.TelegramConfig).first()
    if not config or not config.api_id or not config.api_hash:
        raise HTTPException(status_code=400, detail="Configuración incompleta")
    
    try:
        success = await TelegramService.sign_in_user(
            config.api_id, 
            config.api_hash, 
            request.phone, 
            request.code, 
            request.phone_code_hash, 
            request.password
        )
        if success:
            config.phone = request.phone
            config.is_active = True
            db.commit()
            return {"status": "success", "message": "Autenticación exitosa"}
        else:
            return {"status": "error", "message": "No se pudo autorizar"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Gestión de Permisos Dinámicos (Sólo Superuser) ---

@router.get("/permissions", response_model=List[schemas.ModulePermission])
def get_all_permissions(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user), # All authenticated users can see permissions to adapt UI
) -> Any:
    """
    Obtener la matriz de permisos para todos los roles.
    """
    return db.query(models.ModulePermission).all()

@router.post("/permissions", response_model=List[schemas.ModulePermission])
def update_permissions(
    *,
    db: Session = Depends(deps.get_db),
    permissions_in: List[schemas.ModulePermissionBase],
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Actualiza la matriz de permisos de forma masiva. Solo para el Super Administrador.
    """
    # Limpiamos permisos anteriores para reemplazarlos (simplificación para el MVP)
    # En producción se podría hacer un update selectivo.
    db.query(models.ModulePermission).delete()
    
    for p_in in permissions_in:
        db_p = models.ModulePermission(**p_in.dict())
        db.add(db_p)
    
    db.commit()
    return db.query(models.ModulePermission).all()
