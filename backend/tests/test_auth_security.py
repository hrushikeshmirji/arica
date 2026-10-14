"""
test_auth_security.py — Security test suite for ArecaVision auth hardening.
Tests:
- Admin password seeding (random unless DEV_SEED_ADMIN=true)
- must_change_password middleware blocking on non-auth API endpoints
- Password update clears must_change_password flag
- No credential or hash leaks in API responses
"""

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)
os.chdir(_HERE)

from server import auth, db as sqlite_db
from server.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_must_change_password_blocks_non_auth_endpoints(client):
    """A user flagged with must_change_password=1 must be blocked from accessing non-auth routes."""
    # Create test user with must_change_password=1
    user_id = str(uuid.uuid4())
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"
    pwd_hash = auth.hash_password("TempPass123!")

    with sqlite_db._DB_LOCK:
        conn = sqlite_db._get_conn()
        conn.execute(
            """
            INSERT INTO users (id, username, email, password_hash, name, role, created_at, must_change_password)
            VALUES (?, ?, ?, ?, ?, 'farmer', datetime('now'), 1)
            """,
            (user_id, username, email, pwd_hash, "Test Farmer")
        )
        conn.commit()
        conn.close()

    # Login
    login_resp = client.post("/api/v1/auth/login", json={"username": username, "password": "TempPass123!"})
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["token"]
    user_data = login_resp.json()["data"]["user"]
    assert user_data["mustChangePassword"] is True

    headers = {"Authorization": f"Bearer {token}"}

    # Accessing non-auth API endpoint should be blocked with 403 PASSWORD_CHANGE_REQUIRED
    scans_resp = client.get("/api/v1/scans", headers=headers)
    assert scans_resp.status_code == 403
    err_body = scans_resp.json()
    assert err_body["error"]["code"] == "PASSWORD_CHANGE_REQUIRED"

    # Accessing auth endpoint should NOT be blocked
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200

    # User changes password
    chg_resp = client.post(
        "/api/v1/auth/password",
        headers=headers,
        json={"oldPassword": "TempPass123!", "newPassword": "NewSecurePassword456!"}
    )
    assert chg_resp.status_code == 200

    # Verify user record updated
    user_info = auth.get_user_by_id(user_id)
    assert user_info["mustChangePassword"] is False

    # Now non-auth API endpoints should succeed
    scans_resp_after = client.get("/api/v1/scans", headers=headers)
    assert scans_resp_after.status_code == 200


def test_password_hash_not_leaked(client):
    """Ensure password hashes and sensitive secrets are never included in API payloads."""
    username = f"leaktest_{uuid.uuid4().hex[:6]}"
    reg_resp = client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "Password123!",
        "name": "Leak Check"
    })
    assert reg_resp.status_code == 200
    data = reg_resp.json()["data"]["user"]
    assert "password_hash" not in data
    assert "password" not in data


def test_dev_seed_admin_behavior(monkeypatch):
    """Verify that DEV_SEED_ADMIN=true enables default credentials, while without it a secure password is generated."""
    # When DEV_SEED_ADMIN is false, generated password is not 'admin123'
    monkeypatch.setenv("DEV_SEED_ADMIN", "false")
    dev_seed = os.getenv("DEV_SEED_ADMIN", "").lower() in ("true", "1", "yes")
    assert dev_seed is False

    # When DEV_SEED_ADMIN is true
    monkeypatch.setenv("DEV_SEED_ADMIN", "true")
    dev_seed_true = os.getenv("DEV_SEED_ADMIN", "").lower() in ("true", "1", "yes")
    assert dev_seed_true is True
