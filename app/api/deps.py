from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from ..config.database import SessionLocal
from ..core.security import SECRET_KEY, ALGORITHM
from ..models import User
from ..schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

async def get_current_active_superuser(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="El usuario no tiene suficientes privilegios"
        )
    return current_user
