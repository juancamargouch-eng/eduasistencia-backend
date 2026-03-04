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
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    config = db.query(models.TelegramConfig).first()
    if not config:
        # Create default empty config if not exists
        config = models.TelegramConfig(bot_token="", api_id="", api_hash="", is_active=False)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.post("/telegram", response_model=schemas.TelegramConfig)
def update_telegram_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: schemas.TelegramConfigCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    config = db.query(models.TelegramConfig).first()
    if not config:
        config = models.TelegramConfig(**config_in.dict())
        db.add(config)
    else:
        update_data = config_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    return config

@router.post("/telegram/send-code")
async def send_telegram_code(
    *,
    db: Session = Depends(deps.get_db),
    request: schemas.TelegramCodeRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
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
    current_user: models.User = Depends(deps.get_current_active_user),
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
