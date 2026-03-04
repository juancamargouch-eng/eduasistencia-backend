import requests
import json

def test_register():
    url = "http://localhost:8000/api/students/register"
    
    # Needs authentication!
    # First get token
    login_url = "http://localhost:8000/api/auth/token"
    login_data = {"username": "admin", "password": "admin123"} # Assuming default seed credentials
    
    # Try logging in first
    try:
        session = requests.Session()
        resp = session.post(login_url, data=login_data)
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} {resp.text}")
            # Try with admin/admin just in case seed was different
            login_data = {"username": "admin", "password": "admin"}
            resp = session.post(login_url, data=login_data)
            if resp.status_code != 200:
                print("Login failed with admin/admin too.")
                return

        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Prepare multipart data
        payload = {
            "full_name": "Test Student",
            "grade": "5th",
            "section": "A",
            "face_descriptor": json.dumps([0.1] * 128) # Fake descriptor
        }
        
        # Fake file
        files = {
            "file": ("test.jpg", b"fakeimagebytes", "image/jpeg")
        }
        
        print("Sending register request...")
        r = requests.post(url, headers=headers, data=payload, files=files)
        
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_register()
