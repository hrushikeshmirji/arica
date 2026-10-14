"""
server/db.py — Persistent SQLite Database Layer for ArecaVision AI 2.0.

Provides thread-safe WAL-mode SQLite persistence for:
- Diagnostic Scan History & Clinical Telemetry
- GIS Plantation Digital Twin Blocks (dynamic health score & disease state)
- Epidemiological Alerts & Notifications
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from threading import Lock
from typing import Any

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(_HERE), "data")
os.makedirs(_DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(_DATA_DIR, "arecavision.db")

_DB_LOCK = Lock()


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db() -> None:
    """Initialize SQLite schema and seed default agronomic records if empty."""
    with _DB_LOCK:
        conn = _get_conn()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS plantation_blocks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    trees INTEGER NOT NULL,
                    health_score INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    primary_disease TEXT NOT NULL,
                    last_scanned TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS scans (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    block TEXT NOT NULL,
                    block_id TEXT NOT NULL,
                    disease TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    morphometrics_json TEXT,
                    differential_json TEXT,
                    stage_timings_json TEXT,
                    user_id TEXT DEFAULT NULL
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    msg TEXT NOT NULL,
                    time TEXT NOT NULL,
                    unread INTEGER NOT NULL DEFAULT 1,
                    block_id TEXT
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    ip_address TEXT,
                    details TEXT
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    result_json TEXT,
                    error_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS revoked_tokens (
                    token TEXT PRIMARY KEY,
                    revoked_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                """
            )
            
            # Migration: add user_id to scans if not exists
            try:
                conn.execute("ALTER TABLE scans ADD COLUMN user_id TEXT DEFAULT NULL")
            except sqlite3.OperationalError:
                pass # Column already exists

            # Migration: add must_change_password to users if not exists
            try:
                conn.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            # Seed plantation blocks if empty
            cur = conn.execute("SELECT COUNT(*), COALESCE(SUM(trees), 0) FROM plantation_blocks")
            count_blocks, sum_trees = cur.fetchone()
            default_blocks = [
                ("block-a1", "Block A-1 (North Valley)", 2310, 62, "Critical", "Fruit Rot (Koleroga)", "2 hours ago"),
                ("block-a2", "Block A-2 (North Slope)", 1420, 74, "Warning", "Anthracnose", "4 hours ago"),
                ("block-b1", "Block B-1 (Central Basin)", 1840, 94, "Healthy", "None", "1 day ago"),
                ("block-b2", "Block B-2 (East Ridge)", 1140, 91, "Healthy", "None", "1 day ago"),
                ("block-c1", "Block C-1 (River Bank)", 1890, 58, "Critical", "Yellow Leaf Disease", "3 hours ago"),
                ("block-c2", "Block C-2 (South Terrace)", 1460, 88, "Healthy", "None", "6 hours ago"),
                ("block-d1", "Block D-1 (West Nursery)", 1120, 79, "Warning", "Nut Cracking", "5 hours ago"),
                ("block-d2", "Block D-2 (Highland Plot)", 1360, 95, "Healthy", "None", "2 days ago"),
            ]
            if count_blocks == 0:
                conn.executemany(
                    """
                    INSERT INTO plantation_blocks (id, name, trees, health_score, status, primary_disease, last_scanned)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    default_blocks,
                )
            elif sum_trees != 12540:
                for b_id, _b_name, b_trees, _b_health, _b_status, b_dis, _b_last in default_blocks:
                    conn.execute(
                        "UPDATE plantation_blocks SET trees = ?, primary_disease = ? WHERE id = ?",
                        (b_trees, b_dis, b_id),
                    )

            # Seed initial scan history if empty
            cur = conn.execute("SELECT COUNT(*) FROM scans")
            if cur.fetchone()[0] == 0:
                default_scans = [
                    (
                        "SCN-9042",
                        "2026-09-22 14:32",
                        "Block A-1 (North Valley)",
                        "block-a1",
                        "FruitRot",
                        94.2,
                        "Severe",
                        "Action Required",
                        "https://images.unsplash.com/photo-1596686561350-42716e3d8417?w=300&auto=format&fit=crop&q=80",
                        json.dumps({"healthyPct": 64.2, "chloroticPct": 14.8, "necroticPct": 21.0, "lesionCoveragePct": 35.8}),
                        json.dumps([{"disease": "FruitRot", "probability": 94.2}, {"disease": "Anthracnose", "probability": 4.1}]),
                        json.dumps({"gatekeeperMs": 38, "yoloMs": 92, "vitTtaMs": 240, "xaiRolloutMs": 22, "totalMs": 392}),
                    ),
                    (
                        "SCN-9041",
                        "2026-09-22 11:15",
                        "Block C-1 (River Bank)",
                        "block-c1",
                        "YellowLeaf",
                        91.8,
                        "Severe",
                        "Action Required",
                        "https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=300&auto=format&fit=crop&q=80",
                        json.dumps({"healthyPct": 58.0, "chloroticPct": 31.5, "necroticPct": 10.5, "lesionCoveragePct": 42.0}),
                        json.dumps([{"disease": "YellowLeaf", "probability": 91.8}, {"disease": "Anthracnose", "probability": 5.2}]),
                        json.dumps({"gatekeeperMs": 41, "yoloMs": 88, "vitTtaMs": 255, "xaiRolloutMs": 24, "totalMs": 408}),
                    ),
                    (
                        "SCN-9040",
                        "2026-09-21 16:45",
                        "Block A-2 (North Slope)",
                        "block-a2",
                        "Anthracnose",
                        88.5,
                        "Moderate",
                        "Monitoring",
                        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=300&auto=format&fit=crop&q=80",
                        json.dumps({"healthyPct": 76.4, "chloroticPct": 12.1, "necroticPct": 11.5, "lesionCoveragePct": 23.6}),
                        json.dumps([{"disease": "Anthracnose", "probability": 88.5}, {"disease": "SootyMold", "probability": 6.4}]),
                        json.dumps({"gatekeeperMs": 36, "yoloMs": 95, "vitTtaMs": 232, "xaiRolloutMs": 21, "totalMs": 384}),
                    ),
                    (
                        "SCN-9039",
                        "2026-09-21 09:20",
                        "Block B-1 (Central Basin)",
                        "block-b1",
                        "Healthy",
                        98.4,
                        "Low",
                        "Resolved",
                        "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=300&auto=format&fit=crop&q=80",
                        json.dumps({"healthyPct": 96.2, "chloroticPct": 2.4, "necroticPct": 1.4, "lesionCoveragePct": 3.8}),
                        json.dumps([{"disease": "Healthy", "probability": 98.4}, {"disease": "NutCracking", "probability": 1.1}]),
                        json.dumps({"gatekeeperMs": 34, "yoloMs": 81, "vitTtaMs": 218, "xaiRolloutMs": 19, "totalMs": 352}),
                    ),
                ]
                conn.executemany(
                    """
                    INSERT INTO scans (
                        id, date, block, block_id, disease, confidence, severity,
                        status, image_url, morphometrics_json, differential_json, stage_timings_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    default_scans,
                )

            # Seed initial notifications if empty
            cur = conn.execute("SELECT COUNT(*) FROM notifications")
            if cur.fetchone()[0] == 0:
                default_notifs = [
                    (
                        "ntf-1",
                        "critical",
                        "High Fungal Risk Alert: Block A-1",
                        "Relative humidity exceeded 90% for 48 consecutive hours. Apply 1% Bordeaux mixture immediately to prevent Koleroga outbreak.",
                        "25 mins ago",
                        1,
                        "block-a1",
                    ),
                    (
                        "ntf-2",
                        "warning",
                        "Phytoplasma Vector Activity Detected",
                        "Elevated Proutista moesta (plant hopper) activity in Block C-1. Inspect lower whorl fronds for yellowing.",
                        "2 hours ago",
                        1,
                        "block-c1",
                    ),
                    (
                        "ntf-3",
                        "info",
                        "ArecaVision 2.0 Ensemble Calibrated",
                        "Multi-Scale TTA + LAB Lesion Saliency and SQLite Telemetry Engine active.",
                        "Today",
                        0,
                        None,
                    ),
                ]
                conn.executemany(
                    """
                    INSERT INTO notifications (id, type, title, msg, time, unread, block_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    default_notifs,
                )

            conn.commit()
        finally:
            conn.close()


def get_all_blocks() -> list[dict[str, Any]]:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            rows = conn.execute("SELECT * FROM plantation_blocks ORDER BY id ASC").fetchall()
            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "trees": r["trees"],
                    "healthScore": r["health_score"],
                    "status": r["status"],
                    "primaryDisease": r["primary_disease"],
                    "lastScanned": r["last_scanned"],
                }
                for r in rows
            ]
        finally:
            conn.close()


def update_block(block_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            row = conn.execute("SELECT * FROM plantation_blocks WHERE id = ?", (block_id,)).fetchone()
            if not row:
                return None
            health = updates.get("healthScore", row["health_score"])
            status_val = updates.get("status", row["status"])
            disease = updates.get("primaryDisease", row["primary_disease"])
            last_scanned = updates.get("lastScanned", "Just now")
            conn.execute(
                """
                UPDATE plantation_blocks
                SET health_score = ?, status = ?, primary_disease = ?, last_scanned = ?
                WHERE id = ?
                """,
                (health, status_val, disease, last_scanned, block_id),
            )
            conn.commit()
            updated = conn.execute("SELECT * FROM plantation_blocks WHERE id = ?", (block_id,)).fetchone()
            return {
                "id": updated["id"],
                "name": updated["name"],
                "trees": updated["trees"],
                "healthScore": updated["health_score"],
                "status": updated["status"],
                "primaryDisease": updated["primary_disease"],
                "lastScanned": updated["last_scanned"],
            }
        finally:
            conn.close()


def get_all_scans(limit: int = 50) -> list[dict[str, Any]]:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            rows = conn.execute("SELECT * FROM scans ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
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


def delete_scan(scan_id: str) -> bool:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            cur = conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


_DISEASE_DISPLAY_MAP = {
    "Anthracnose": "Anthracnose",
    "BudBorer": "Bud Borer",
    "FruitRot": "Fruit Rot (Koleroga)",
    "Healthy": "Healthy",
    "LeafSpotComplex": "Leaf Spot Complex",
    "NutCracking": "Nut Cracking",
    "PhytoplasmaYellowLeaf": "Phytoplasma Yellow Leaf",
    "SootyMold": "Sooty Mold",
    "StemBleeding": "Stem Bleeding",
    "StemCracking": "Stem Cracking",
    "YellowLeaf": "Yellow Leaf Disease",
}


def format_disease_display(raw_label: str) -> str:
    return _DISEASE_DISPLAY_MAP.get(raw_label, raw_label)


def get_notifications() -> dict[str, Any]:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            rows = conn.execute("SELECT * FROM notifications ORDER BY rowid DESC LIMIT 25").fetchall()
            items = [
                {
                    "id": r["id"],
                    "type": r["type"],
                    "title": r["title"],
                    "msg": r["msg"],
                    "time": r["time"],
                    "unread": bool(r["unread"]),
                    "blockId": r["block_id"],
                }
                for r in rows
            ]
            unread_count = sum(1 for i in items if i["unread"])
            return {"notifications": items, "unreadCount": unread_count}
        finally:
            conn.close()


def mark_all_notifications_read() -> None:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            conn.execute("UPDATE notifications SET unread = 0")
            conn.commit()
        finally:
            conn.close()


def mark_notification_read(notif_id: str) -> None:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            conn.execute("UPDATE notifications SET unread = 0 WHERE id = ?", (notif_id,))
            conn.commit()
        finally:
            conn.close()


def record_scan_and_sync_twin(
    *,
    disease: str,
    confidence: float,
    severity: str,
    block_id: str = "block-a1",
    morphometrics: dict[str, Any] | None = None,
    differential: list[dict[str, Any]] | None = None,
    stage_timings: dict[str, Any] | None = None,
    user_id: str | None = None,
    image_url: str | None = None,
) -> dict[str, Any]:
    """Persist a completed diagnostic scan and automatically update the target Plantation Block & Notifications."""
    if disease == "Not an Arecanut image":
        return {}

    display_disease = format_disease_display(disease)

    with _DB_LOCK:
        conn = _get_conn()
        try:
            block_row = conn.execute("SELECT * FROM plantation_blocks WHERE id = ?", (block_id,)).fetchone()
            if not block_row:
                block_row = conn.execute("SELECT * FROM plantation_blocks LIMIT 1").fetchone()
            block_name = block_row["name"] if block_row else "Block A-1 (North Valley)"
            actual_block_id = block_row["id"] if block_row else "block-a1"

            scan_id = f"SCN-{uuid.uuid4().hex[:8].upper()}"
            while conn.execute("SELECT 1 FROM scans WHERE id = ?", (scan_id,)).fetchone():
                scan_id = f"SCN-{uuid.uuid4().hex[:8].upper()}"
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

            if disease == "Healthy":
                status_str = "Resolved"
            elif severity in ("Severe", "High", "Critical"):
                status_str = "Action Required"
            else:
                status_str = "Monitoring"

            img_url = (
                image_url
                if image_url
                else (
                    "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=300&auto=format&fit=crop&q=80"
                    if disease == "Healthy"
                    else "https://images.unsplash.com/photo-1596686561350-42716e3d8417?w=300&auto=format&fit=crop&q=80"
                )
            )

            conn.execute(
                """
                INSERT INTO scans (
                    id, date, block, block_id, disease, confidence, severity,
                    status, image_url, morphometrics_json, differential_json, stage_timings_json, user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    now_str,
                    block_name,
                    actual_block_id,
                    disease,
                    round(confidence, 1),
                    severity,
                    status_str,
                    img_url,
                    json.dumps(morphometrics or {}),
                    json.dumps(differential or []),
                    json.dumps(stage_timings or {}),
                    user_id,
                ),
            )

            # Update the GIS Plantation Block health & status dynamically
            if block_row:
                old_health = int(block_row["health_score"])
                if disease == "Healthy":
                    new_health = min(98, max(85, old_health + 6))
                    new_status = "Healthy"
                    new_disease = "None"
                elif severity in ("Severe", "Critical"):
                    new_health = max(42, min(65, old_health - 8))
                    new_status = "Critical"
                    new_disease = display_disease
                else:
                    new_health = max(66, min(82, old_health - 4))
                    new_status = "Warning"
                    new_disease = display_disease

                conn.execute(
                    """
                    UPDATE plantation_blocks
                    SET health_score = ?, status = ?, primary_disease = ?, last_scanned = ?
                    WHERE id = ?
                    """,
                    (new_health, new_status, new_disease, "Just now", actual_block_id),
                )

                # Create real-time notification if diseased
                if disease != "Healthy":
                    ntf_id = f"ntf-{uuid.uuid4().hex[:6]}"
                    ntf_type = "critical" if severity in ("Severe", "Critical") else "warning"
                    conn.execute(
                        """
                        INSERT INTO notifications (id, type, title, msg, time, unread, block_id)
                        VALUES (?, ?, ?, ?, ?, 1, ?)
                        """,
                        (
                            ntf_id,
                            ntf_type,
                            f"{display_disease} Detected in {block_name}",
                            f"AI Diagnostic Studio recorded {display_disease} ({confidence:.1f}% confidence, {severity} severity). Immediate phytosanitary intervention advised.",
                            "Just now",
                            actual_block_id,
                        ),
                    )

            conn.commit()
            return {"scanId": scan_id, "blockId": actual_block_id, "blockName": block_name}
        finally:
            conn.close()


def log_audit_event(action: str, user_id: str | None = None, ip_address: str | None = None, details: str = "") -> None:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            conn.execute(
                """
                INSERT INTO audit_logs (id, timestamp, user_id, action, ip_address, details)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f"log-{uuid.uuid4().hex[:8]}",
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    user_id or "anonymous",
                    action,
                    ip_address or "127.0.0.1",
                    details,
                ),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()


def get_audit_logs(limit: int = 50) -> list[dict[str, Any]]:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
            return [
                {
                    "id": r["id"],
                    "timestamp": r["timestamp"],
                    "userId": r["user_id"],
                    "action": r["action"],
                    "ipAddress": r["ip_address"],
                    "details": r["details"],
                }
                for r in rows
            ]
        finally:
            conn.close()


def change_user_password(user_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
    import bcrypt
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."
    with _DB_LOCK:
        conn = _get_conn()
        try:
            row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                return False, "User not found."
            current_hash = row["password_hash"].encode("utf-8")
            if not bcrypt.checkpw(old_password.encode("utf-8"), current_hash):
                return False, "Incorrect current password."
            new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            conn.execute("UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?", (new_hash, user_id))
            conn.commit()
            return True, "Password updated successfully."
        finally:
            conn.close()


def create_job(job_id: str, stage: str = "queued") -> None:
    now_str = datetime.now(timezone.utc).isoformat()
    with _DB_LOCK:
        conn = _get_conn()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs (id, status, stage, progress, result_json, error_json, created_at, updated_at)
                VALUES (?, 'processing', ?, 10, NULL, NULL, ?, ?)
                """,
                (job_id, stage, now_str, now_str),
            )
            conn.commit()
        finally:
            conn.close()


def update_job(
    job_id: str,
    status: str,
    stage: str,
    progress: int = 0,
    result: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> None:
    now_str = datetime.now(timezone.utc).isoformat()
    res_str = json.dumps(result) if result else None
    err_str = json.dumps(error) if error else None
    with _DB_LOCK:
        conn = _get_conn()
        try:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, stage = ?, progress = ?, result_json = COALESCE(?, result_json), error_json = COALESCE(?, error_json), updated_at = ?
                WHERE id = ?
                """,
                (status, stage, progress, res_str, err_str, now_str, job_id),
            )
            conn.commit()
        finally:
            conn.close()


def get_job(job_id: str) -> dict[str, Any] | None:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            res = None
            if row["result_json"]:
                try:
                    res = json.loads(row["result_json"])
                except Exception:
                    pass
            err = None
            if row["error_json"]:
                try:
                    err = json.loads(row["error_json"])
                except Exception:
                    pass
            return {
                "job_id": row["id"],
                "status": row["status"],
                "stage": row["stage"],
                "progress": row["progress"],
                "result": res,
                "error": err,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        finally:
            conn.close()


def add_revoked_token(token: str, expires_at: str) -> None:
    now_str = datetime.now(timezone.utc).isoformat()
    with _DB_LOCK:
        conn = _get_conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO revoked_tokens (token, revoked_at, expires_at) VALUES (?, ?, ?)",
                (token, now_str, expires_at),
            )
            conn.commit()
        finally:
            conn.close()


def is_token_revoked_db(token: str) -> bool:
    with _DB_LOCK:
        conn = _get_conn()
        try:
            row = conn.execute("SELECT 1 FROM revoked_tokens WHERE token = ?", (token,)).fetchone()
            return row is not None
        finally:
            conn.close()


# Ensure database is initialized on module import
init_db()
