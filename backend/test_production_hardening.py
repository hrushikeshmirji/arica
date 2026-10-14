import requests
import sys
import json
import time

BASE_URL = "http://localhost:8000"

def log_test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name} {f'- {detail}' if detail else ''}")
    if not passed:
        sys.exit(1)

def unwrap(res):
    try:
        j = res.json()
        if isinstance(j, dict) and "data" in j:
            return j["data"]
        return j
    except Exception:
        return res.text

def main():
    print("=== ArecaVision Enterprise Production Hardening Verification ===")
    
    # 1. Security Headers Verification
    res = requests.get(f"{BASE_URL}/api/v1/health")
    headers = res.headers
    log_test(
        "Security Headers: X-Content-Type-Options", 
        headers.get("X-Content-Type-Options") == "nosniff",
        headers.get("X-Content-Type-Options")
    )
    log_test(
        "Security Headers: X-Frame-Options", 
        headers.get("X-Frame-Options") == "DENY",
        headers.get("X-Frame-Options")
    )
    log_test(
        "Security Headers: Referrer-Policy", 
        headers.get("Referrer-Policy") == "strict-origin-when-cross-origin",
        headers.get("Referrer-Policy")
    )

    # 2. Admin Authentication
    admin_login = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username": "admin",
        "password": "adminpassword"
    })
    if admin_login.status_code != 200:
        admin_login = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
    log_test(
        "Admin Authentication",
        admin_login.status_code == 200,
        f"Status: {admin_login.status_code}"
    )
    login_data = unwrap(admin_login)
    admin_token = login_data.get("token")
    assert admin_token, f"Failed to extract token: {login_data}"
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Dynamic Epidemiological Risk Engine
    risk_res = requests.get(f"{BASE_URL}/api/v1/risk/forecast", headers=admin_headers)
    risk_data = unwrap(risk_res)
    log_test(
        "Epidemiological Risk Forecast API",
        risk_res.status_code == 200 and "compositeIndex" in risk_data,
        f"Overall Index: {risk_data.get('compositeIndex')}, Severity: {risk_data.get('overallSeverity')}"
    )
    assert "trajectory" in risk_data and len(risk_data["trajectory"]) > 0, "Missing trajectory"
    assert "blockVulnerability" in risk_data and len(risk_data["blockVulnerability"]) > 0, "Missing blocks"
    assert "pathogenMetrics" in risk_data, "Missing pathogens"

    # 4. Dynamic Analytics Overview
    analytics_res = requests.get(f"{BASE_URL}/api/v1/analytics/overview", headers=admin_headers)
    analytics_data = unwrap(analytics_res)
    log_test(
        "Dynamic Analytics Overview API",
        analytics_res.status_code == 200 and "estimatedYieldTons" in analytics_data,
        f"Yield: {analytics_data.get('estimatedYieldTons')} tons, Control Rate: {analytics_data.get('diseaseControlRate')}%"
    )

    # 5. Real Reports Generation - CSV Export
    csv_res = requests.post(
        f"{BASE_URL}/api/v1/reports/export",
        json={"format": "csv", "include_confidence": True},
        headers=admin_headers
    )
    log_test(
        "Report Export (CSV)",
        csv_res.status_code == 200 and "text/csv" in csv_res.headers.get("content-type", ""),
        f"Bytes: {len(csv_res.content)}, Header preview: {csv_res.text.splitlines()[0] if csv_res.text else ''}"
    )

    # 6. Real Reports Generation - Printable Audit Certificate
    pdf_res = requests.post(
        f"{BASE_URL}/api/v1/reports/export",
        json={"format": "pdf", "include_confidence": True},
        headers=admin_headers
    )
    log_test(
        "Report Export (Printable Certificate)",
        pdf_res.status_code == 200 and "text/html" in pdf_res.headers.get("content-type", "") and "ArecaVision AI" in pdf_res.text,
        f"Bytes: {len(pdf_res.content)}, Contains Cryptographic Stamp: {'SHA256' in pdf_res.text}"
    )

    # 7. User Registration & Password Change Lifecycle
    test_user = f"tester_{int(time.time())}"
    reg_res = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "username": test_user,
        "email": f"{test_user}@arecavision.test",
        "name": "Test Agronomist",
        "fullName": "Test Agronomist",
        "password": "Password123!",
        "role": "agronomist"
    })
    reg_data = unwrap(reg_res)
    log_test(
        "User Registration Lifecycle",
        reg_res.status_code == 200 and "token" in reg_data,
        f"Created user: {test_user}"
    )
    user_token = reg_data["token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Change password
    pwd_res = requests.post(f"{BASE_URL}/api/v1/auth/password", json={
        "oldPassword": "Password123!",
        "newPassword": "NewSecretPass456!"
    }, headers=user_headers)
    pwd_data = unwrap(pwd_res)
    log_test(
        "User Password Change API",
        pwd_res.status_code == 200,
        f"Result: {pwd_data}"
    )

    # Login with old password (must fail)
    old_login = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username": test_user,
        "password": "Password123!"
    })
    log_test(
        "Old Password Invalidation",
        old_login.status_code == 401,
        f"Status: {old_login.status_code} (Expected 401)"
    )

    # Login with new password (must succeed)
    new_login = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username": test_user,
        "password": "NewSecretPass456!"
    })
    log_test(
        "New Password Authentication",
        new_login.status_code == 200,
        f"Status: {new_login.status_code} (Token issued)"
    )

    # 8. Security Audit Trail Logs
    audit_res = requests.get(f"{BASE_URL}/api/v1/admin/audit-logs?limit=20", headers=admin_headers)
    audit_data = unwrap(audit_res)
    log_test(
        "Security Audit Trail API",
        audit_res.status_code == 200 and isinstance(audit_data, list),
        f"Retrieved {len(audit_data)} audit log records"
    )
    actions = [log["action"] for log in audit_data]
    print(f"  Audited actions in system: {set(actions)}")

    # 9. One-Click SQLite Database Backup API
    backup_res = requests.get(f"{BASE_URL}/api/v1/admin/db/backup", headers=admin_headers)
    log_test(
        "Admin Database Snapshot Backup API",
        backup_res.status_code == 200 and len(backup_res.content) > 1000,
        f"Downloaded {len(backup_res.content)} bytes, Content-Type: {backup_res.headers.get('content-type')}"
    )

    # 10. Forensic Audit Trail CSV Export API
    csv_audit_res = requests.get(f"{BASE_URL}/api/v1/admin/audit-logs/export-csv", headers=admin_headers)
    log_test(
        "Admin Forensic Audit CSV Export API",
        csv_audit_res.status_code == 200 and "text/csv" in csv_audit_res.headers.get("content-type", ""),
        f"Exported {len(csv_audit_res.content)} bytes, Preview: {csv_audit_res.text.splitlines()[0] if csv_audit_res.text else ''}"
    )

    # 11. Admin System Stats & Operations API
    stats_res = requests.get(f"{BASE_URL}/api/v1/admin/system-stats", headers=admin_headers)
    stats_data = unwrap(stats_res)
    log_test(
        "Admin System Telemetry & Storage API",
        stats_res.status_code == 200 and "databaseSizeFormatted" in stats_data,
        f"DB Size: {stats_data.get('databaseSizeFormatted')}, Users: {stats_data.get('usersCount')}, Scans: {stats_data.get('scansCount')}"
    )

    # 12. Public Certificate Verification API & SVG QR Integrity
    cert_verify_res = requests.get(f"{BASE_URL}/api/v1/verify/CERT-AUTOMATED-TEST")
    cert_data = unwrap(cert_verify_res)
    log_test(
        "Public Diagnostic Certificate Verification API",
        cert_verify_res.status_code == 200 and cert_data.get("valid") is True,
        f"Status: {cert_data.get('status')}, Authority: {cert_data.get('authority')}"
    )

    # 13. Persistent Diagnostic Job Queue & Verified Static Asset Pipeline
    detect_res = requests.post(f"{BASE_URL}/api/v1/detect?specimen_id=fruit_rot")
    detect_data = unwrap(detect_res)
    job_id = detect_data.get("job_id") if isinstance(detect_data, dict) else None
    log_test("Detection Job Dispatch", bool(job_id), f"Job ID: {job_id}")

    job_completed = False
    start_time = time.time()
    result_data = None
    while time.time() - start_time < 20:
        poll_res = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}")
        poll_data = unwrap(poll_res)
        if isinstance(poll_data, dict) and poll_data.get("status") == "done":
            job_completed = True
            result_data = poll_data.get("result", {})
            break
        time.sleep(0.5)

    log_test(
        "Persistent Background Inference Pipeline",
        job_completed and result_data and result_data.get("disease") != "",
        f"Diagnosed: {result_data.get('diseaseDisplayName')}, Conf: {result_data.get('confidence')}%"
    )

    img_url = result_data.get("imageUrl") if result_data else ""
    img_valid = False
    if img_url:
        static_img_res = requests.get(f"{BASE_URL}{img_url}")
        img_valid = static_img_res.status_code == 200 and len(static_img_res.content) > 1000

    log_test(
        "Static Image Asset Persistence (/uploads)",
        img_valid,
        f"Path: {img_url}"
    )

    print("\n=======================================================")
    print(" ALL PRODUCTION HARDENING & ENTERPRISE CHECKS PASSED! ")
    print("=======================================================")

if __name__ == "__main__":
    main()
