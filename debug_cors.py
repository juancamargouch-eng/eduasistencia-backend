import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test():
    print(f"Testing connectivity to {BASE_URL}...")
    try:
        # 1. Test OPTIONS
        print("[1] Testing OPTIONS /api/students/1...")
        r = requests.options(f"{BASE_URL}/api/students/1", 
                             headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "DELETE"},
                             timeout=5)
        print(f"   -> Status: {r.status_code}")
        
        # 2. Login
        print("[2] Logging in to get token (admin/admin123)...")
        login = requests.post(f"{BASE_URL}/api/auth/token", 
                              data={"username": "admin", "password": "admin123"},
                              timeout=10)
        
        if login.status_code != 200:
            print(f"   -> Login FAILED: {login.status_code} {login.text}")
            return
            
        token = login.json()["access_token"]
        print(f"   -> Got token: {token[:10]}...")
        
        # 3. Test DELETE
        print("[3] Testing DELETE /api/students/1...")
        r_del = requests.delete(f"{BASE_URL}/api/students/1", 
                                headers={"Authorization": f"Bearer {token}", "Origin": "http://localhost:5173"},
                                timeout=10)
        print(f"   -> DELETE Status: {r_del.status_code}")
        print(f"   -> DELETE Response: {r_del.text}")
        
    except requests.exceptions.Timeout:
        print("   -> Request TIMED OUT")
    except requests.exceptions.ConnectionError:
        print("   -> Connection REFUSED (Server likely down)")
    except Exception as e:
        print(f"   -> ERROR: {e}")

if __name__ == "__main__":
    for i in range(5):
        print(f"\n--- Attempt {i+1}/5 ---")
        try:
            test()
            # If we got here without exception, likely connected (even if status is error)
            # But let's break only if we got a response
            break 
        except Exception:
            pass
        time.sleep(2)
