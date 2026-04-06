import os
import sys

# Ajustar path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("Intentando hacer petición a /api/auth/token...")
response = client.post("/api/auth/token", data={"username": "admin", "password": "adminpassword"})
print("Status Code:", response.status_code)
print("Response:", response.text)
