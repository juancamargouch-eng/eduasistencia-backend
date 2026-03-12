from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.core import security
from app.api import deps

router = APIRouter()

@router.get("/me", response_model=schemas.user.User)
def read_user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.put("/me", response_model=schemas.user.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.user.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    # Verificar si el nombre de usuario ya existe (si se está cambiando)
    if user_in.username is not None and user_in.username != current_user.username:
        user = db.query(models.User).filter(models.User.username == user_in.username).first()
        if user:
            raise HTTPException(
                status_code=400,
                detail="El nombre de usuario ya está en uso.",
            )
        current_user.username = user_in.username
    
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    
    if user_in.password is not None and user_in.password != "":
        current_user.hashed_password = security.get_password_hash(user_in.password)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
