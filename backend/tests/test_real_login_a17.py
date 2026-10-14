import os
import json
import sqlite3
import requests

RESULTS_DIR = r"D:\ArecaVision_Combined\backend\tests\results"
os.makedirs(RESULTS_DIR, exist_ok=True)
DB_PATH = r"D:\ArecaVision_Combined\backend\data\arecavision.db"

BASE_URL = "http://127.0.0.1:8000/api/v1"

def main():
    print("--- 1. POST /api/v1/auth/login ---")
    login_payload = {
        "username": "admin",
        "password": "admin123"
    }
    resp_login = requests.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=10)
    print(f"HTTP Status: {resp_login.status_code}")
    print(f"Raw Response Body:\n{resp_login.text}")

    token = None
    if resp_login.status_code == 200:
        login_data = resp_login.json()
        token = login_data.get("data", {}).get("token") or login_data.get("token")

    print("\n--- 2. GET /api/v1/auth/me with Bearer Token ---")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp_me = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
    print(f"HTTP Status: {resp_me.status_code}")
    print(f"Raw Response Body:\n{resp_me.text}")

    # 3. Query all users from DB
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    db_users = cur.execute("SELECT id, username, email, name, role, must_change_password FROM users").fetchall()
    con.close()

    user_list = []
    for u in db_users:
        user_list.append({
            "id": u[0],
            "username": u[1],
            "email": u[2],
            "name": u[3],
            "role": u[4],
            "must_change_password": bool(u[5])
        })

    print("\n--- 3. Database Users & Roles ---")
    header = f"{'Username':<22} | {'Email':<32} | {'Role':<8} | {'Must Change Pwd':<16}"
    print(header)
    print("-" * len(header))
    for u in user_list:
        print(f"{u['username']:<22} | {u['email']:<32} | {u['role']:<8} | {str(u['must_change_password']):<16}")

    auth_results = {
        "login_request": {
            "url": f"{BASE_URL}/auth/login",
            "username": "admin",
            "status_code": resp_login.status_code,
            "response_json": resp_login.json() if resp_login.status_code == 200 else resp_login.text
        },
        "me_request": {
            "url": f"{BASE_URL}/auth/me",
            "status_code": resp_me.status_code,
            "response_json": resp_me.json() if resp_me.status_code == 200 else resp_me.text
        },
        "default_credentials_exist": True,
        "default_credentials": "admin / admin123 (seeded on startup in auth.py)",
        "must_change_password_enforced": False,
        "must_change_password_details": "must_change_password is a column in SQLite and returned as mustChangePassword boolean flag in response, but backend routes do not intercept or block user requests when must_change_password=1.",
        "users": user_list
    }

    out_file = os.path.join(RESULTS_DIR, "auth_check.json")
    with open(out_file, "w") as f:
        json.dump(auth_results, f, indent=2)
    print(f"\nSaved auth check to {out_file}")

if __name__ == "__main__":
    main()
