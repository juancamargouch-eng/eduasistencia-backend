import random
import json
from locust import HttpUser, task, between

class AttendanceUser(HttpUser):
    wait_time = between(0.01, 0.05)
    student_dnis = []

    def on_start(self):
        # Intentar cargar DNIs directamente una vez al inicio del test manager
        # Usaremos una lista precargada para evitar dependencias de la API en el arranque
        try:
            # Esta es una simplificación: si la API falla, usamos una lista vacía y fallamos la tarea
            response = self.client.get("/api/students/?skip=0&limit=2500", name="/api/students/all")
            if response.status_code == 200:
                data = response.json()
                self.student_dnis = [s["dni"] for s in data.get("items", []) if s.get("dni")]
                print(f"DEBUG: Cargados {len(self.student_dnis)} DNIs")
        except Exception as e:
            print(f"DEBUG ERROR: {e}")

    @task
    def verify_attendance(self):
        if not self.student_dnis:
            # Reintentar carga si falló
            self.on_start()
            if not self.student_dnis: return

        dni = random.choice(self.student_dnis)
        face_descriptor = [random.uniform(-0.1, 0.2) for _ in range(224)]
        
        payload = {
            "dni": dni,
            "face_descriptor": json.dumps(face_descriptor),
            "event_type": "ENTRY"
        }
        
        headers = {"X-Stress-Test": "true"}
        self.client.post("/api/attendance/verify", data=payload, headers=headers)

    @task(1)
    def view_occupancy(self):
        self.client.get("/api/attendance/stats/occupancy")
