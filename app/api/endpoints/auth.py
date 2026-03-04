from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.core import security
from app.api import deps

router = APIRouter()

@router.post("/token", response_model=schemas.user.Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
