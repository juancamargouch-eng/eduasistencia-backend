import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.api.endpoints.students import photo_proxy
from fastapi import HTTPException

load_dotenv()

async def debug_proxy_call():
    db = SessionLocal()
    # Usar la key de Félix Huamani que ya sabemos que existe
    key = "f5-ae44-388183edfea7.jpg"
    
    # Simular una firma válida (o saltar auth para debug)
    # En el código, si no hay token ni sig, falla.
    # Vamos a pasar una firma manual calculada como el backend espera
    import hmac
    import hashlib
    secret = os.getenv("SECRET_KEY", "eduasistencia-secret-key")
    signature = hmac.new(
        secret.encode(),
        key.encode(),
        hashlib.sha256
    ).hexdigest()
    
    print(f"Probando proxy con Key: {key} y Sig: {signature}")
    
    try:
        # El endpoint es una función async (si lo convertí a async, o si es def)
        # Students.py: @router.get("/photo-proxy") async def photo_proxy(...)
        response = await photo_proxy(key=key, sig=signature, db=db)
        print("¡ÉXITO! El proxy devolvió una respuesta.")
        print(f"Tipo de respuesta: {type(response)}")
        if hasattr(response, "status_code"):
            print(f"Status: {response.status_code}")
    except HTTPException as e:
        print(f"HTTP Error {e.status_code}: {e.detail}")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_proxy_call())
