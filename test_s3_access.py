import os
import requests
from dotenv import load_dotenv
from app.services.storage_service import StorageService

load_dotenv()

def test_url_access():
    key = "eduasistencia/fotos-estudiantes/f5-ae44-388183edfea7.jpg"
    print(f"Generando URL firmada para: {key}")
    
    url = StorageService.get_presigned_url(key)
    if not url:
        print("Fallo al generar URL.")
        return
        
    print(f"URL: {url}")
    print("Intentando descargar...")
    
    try:
        r = requests.get(url, timeout=10)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            print("¡ÉXITO! La URL es accesible.")
        else:
            print(f"ERROR: Respuesta del servidor: {r.text[:200]}")
    except Exception as e:
        print(f"ERROR DE CONEXION: {e}")

if __name__ == "__main__":
    test_url_access()
