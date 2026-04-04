from typing import Any, Optional, List
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

# --- Gestión de Usuarios (Sólo Superuser) ---

@router.get("/", response_model=List[schemas.user.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Lista todos los usuarios del sistema. Solo para el Super Administrador.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=schemas.user.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.user.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Crea un nuevo usuario con un rol determinado.
    """
    user = db.query(models.User).filter(models.User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Este nombre de usuario ya existe en el sistema.",
        )
    
    # Preparamos el nuevo usuario
    db_obj = models.User(
        username=user_in.username,
        full_name=user_in.full_name,
        email=user_in.email,
        role=user_in.role,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        hashed_password=security.get_password_hash(user_in.password),
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.put("/{user_id}", response_model=schemas.user.User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.user.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Actualiza cualquier usuario. Incluyendo el cambio de rol.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = user_in.dict(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        db_user.hashed_password = security.get_password_hash(update_data["password"])
        del update_data["password"]
        
    for field, value in update_data.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)
            
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", response_model=schemas.user.User)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Elimina un usuario de forma definitiva.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta de Super Administrador")
        
    db.delete(db_user)
    db.commit()
    return db_user
