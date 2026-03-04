from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func
from app import models, schemas
from app.api import deps
from pydantic import BaseModel

router = APIRouter()

class DeviceCreate(BaseModel):
    name: str
    location: str
    device_type: str = "KIOSK"
    ip_address: str = None

class DeviceHeartbeat(BaseModel):
    device_id: int
    ip_address: str = None

@router.get("/", response_model=List[dict])
def read_devices(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    devices = db.query(models.Device).all()
    # Annotate with online status (e.g. last heartbeat < 2 mins ago)
    results = []
    now = datetime.now().astimezone() # Use aware datetime if possible, or naive
    # Ideally use server database time, but for now simple check
    for d in devices:
        is_online = False
        if d.last_heartbeat:
            # Assuming last_heartbeat is naive or aware matching system
             pass # Logic handles in frontend or simple calc here?
             # Let's just return raw and let frontend decide or calc here
        
        results.append({
            "id": d.id,
            "name": d.name,
            "location": d.location,
            "is_active": d.is_active,
            "last_heartbeat": d.last_heartbeat,
            "ip_address": d.ip_address,
            "device_type": d.device_type
        })
    return results

@router.post("/", response_model=dict)
def create_device(
    *,
    db: Session = Depends(deps.get_db),
    device_in: DeviceCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    device = models.Device(
        name=device_in.name,
        location=device_in.location,
        device_type=device_in.device_type,
        ip_address=device_in.ip_address
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return {"id": device.id, "name": device.name}

@router.post("/heartbeat")
def heartbeat(
    *,
    db: Session = Depends(deps.get_db),
    heartbeat_in: DeviceHeartbeat,
    # No auth required for heartbeat? Or maybe basic? 
    # For now open to ease kiosk implementation or simple token
) -> Any:
    device = db.query(models.Device).filter(models.Device.id == heartbeat_in.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    device.last_heartbeat = func.now()
    if heartbeat_in.ip_address:
        device.ip_address = heartbeat_in.ip_address
        
    db.commit()
    return {"status": "ok"}
