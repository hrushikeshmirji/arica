import os
import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import Any
from server.db import _DB_LOCK, _get_conn, get_all_scans

JWT_SECRET = os.getenv("JWT_SECRET", "ARECAVISION_AI_ENTERPRISE_SECRET_KEY_2026_PRODUCTION")
JWT_ALGORITHM = "HS256"

def init_auth_tables() -> None:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'farmer',
                    created_at TEXT NOT NULL,
                    last_login TEXT
                );
                """
            )
            
            # Migration: add must_change_password column
            try:
                conn.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0")
            except Exception:
                pass

            # Seed admin user
            cur = conn.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            if cur.fetchone()[0] == 0:
                import secrets
                import string
                admin_id = str(uuid.uuid4())
                now_str = datetime.now(timezone.utc).isoformat()
                dev_seed = os.getenv("DEV_SEED_ADMIN", "").lower() in ("true", "1", "yes")
                if dev_seed:
                    initial_password = "admin123"
                    must_change = 1
                else:
                    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
                    initial_password = "".join(secrets.choice(alphabet) for _ in range(18))
                    must_change = 1
                    print(f"[SECURITY] Generated initial random admin password: {initial_password}")
                    print("[SECURITY] Admin must change password on first login.")
                pwd_hash = hash_password(initial_password)
                conn.execute(
                    """
                    INSERT INTO users (id, username, email, password_hash, name, role, created_at, must_change_password)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (admin_id, 'admin', 'admin@arecavision.ai', pwd_hash, 'Administrator', 'admin', now_str, must_change)
                )
            conn.commit()
        finally:
            conn.close()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        return False

def create_jwt(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def register_user(username: str, email: str, password: str, name: str) -> dict:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            # Check if user exists
            cur = conn.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cur.fetchone():
                raise ValueError("Username or email already exists")

            user_id = str(uuid.uuid4())
            now_str = datetime.now(timezone.utc).isoformat()
            pwd_hash = hash_password(password)
            
            conn.execute(
                """
                INSERT INTO users (id, username, email, password_hash, name, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, username, email, pwd_hash, name, 'farmer', now_str)
            )
            conn.commit()
            
            return {
                "id": user_id,
                "username": username,
                "email": email,
                "name": name,
                "role": 'farmer',
                "created_at": now_str
            }
        finally:
            conn.close()

def authenticate_user(username: str, password: str) -> dict | None:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            cur = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
            row = cur.fetchone()
            if not row:
                return None
            
            if not verify_password(password, row['password_hash']):
                return None
                
            now_str = datetime.now(timezone.utc).isoformat()
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, row['id']))
            conn.commit()
            
            user = dict(row)
            del user['password_hash']
            user['mustChangePassword'] = bool(user.get('must_change_password', 0))
            token = create_jwt(user['id'], user['role'])
            
            return {
                "user": user,
                "token": token
            }
        finally:
            conn.close()

def get_user_by_id(user_id: str) -> dict | None:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                return None
            user = dict(row)
            del user['password_hash']
            user['mustChangePassword'] = bool(user.get('must_change_password', 0))
            return user
        finally:
            conn.close()

def get_all_users() -> list[dict]:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            # Need to get scan counts per user as per prompt
            cur = conn.execute(
                """
                SELECT u.*, COUNT(s.id) as scan_count 
                FROM users u 
                LEFT JOIN scans s ON u.id = s.user_id 
                GROUP BY u.id
                """
            )
            users = []
            for row in cur.fetchall():
                user = dict(row)
                del user['password_hash']
                users.append(user)
            return users
        finally:
            conn.close()

def get_user_scans(user_id: str) -> list[dict]:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            rows = conn.execute("SELECT * FROM scans WHERE user_id = ? ORDER BY rowid DESC", (user_id,)).fetchall()
            import json
            result = []
            for r in rows:
                item: dict[str, Any] = {
                    "id": r["id"],
                    "date": r["date"],
                    "block": r["block"],
                    "blockId": r["block_id"],
                    "disease": r["disease"],
                    "confidence": r["confidence"],
                    "severity": r["severity"],
                    "status": r["status"],
                    "imageUrl": r["image_url"],
                    "userId": r["user_id"]
                }
                if r["morphometrics_json"]:
                    try:
                        item["tissueMorphometrics"] = json.loads(r["morphometrics_json"])
                    except Exception:
                        pass
                if r["differential_json"]:
                    try:
                        item["differentialDiagnosis"] = json.loads(r["differential_json"])
                    except Exception:
                        pass
                if r["stage_timings_json"]:
                    try:
                        item["stageTimingsMs"] = json.loads(r["stage_timings_json"])
                    except Exception:
                        pass
                result.append(item)
            return result
        finally:
            conn.close()
