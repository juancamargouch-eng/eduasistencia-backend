from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.announcement.Announcement])
def read_announcements(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_docente),
) -> Any:
    """
    Retrieve announcements.
    """
    announcements = db.query(models.Announcement).offset(skip).limit(limit).all()
    return announcements

@router.post("/", response_model=schemas.announcement.Announcement)
async def create_announcement(
    *,
    db: Session = Depends(deps.get_db),
    announcement_in: schemas.announcement.AnnouncementCreate,
    current_user: models.User = Depends(deps.get_current_active_docente),
) -> Any:
    """
    Create new announcement.
    """
    announcement = models.Announcement(
        **announcement_in.dict(),
        author_id=current_user.id
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    
    # Pendiente: Integración con Telegram aquí si se confirma
    
    return announcement

@router.delete("/{id}", response_model=schemas.announcement.Announcement)
def delete_announcement(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_docente),
) -> Any:
    """
    Delete an announcement.
    """
    announcement = db.query(models.Announcement).filter(models.Announcement.id == id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Comunicado no encontrado")
    
    if not current_user.is_superuser and current_user.role != "ADMIN" and announcement.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este comunicado")
        
    db.delete(announcement)
    db.commit()
    return announcement
