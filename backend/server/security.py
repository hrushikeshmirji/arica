"""
server/security.py — Enterprise security utilities & middleware for ArecaVision AI.

Includes:
- Sliding-window in-memory rate limiting middleware
- Standard HTTP security headers middleware
- Magic byte image file verification and sanitization
- Revoked token blacklist management
"""

import io
import time
import threading
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from PIL import Image

# ---------------------------------------------------------------------------
# Rate Limiting Engine (Sliding Window per IP)
# ---------------------------------------------------------------------------
class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        auth_limit: int = 10,       # Max auth attempts per minute
        detect_limit: int = 30,     # Max ML inference requests per minute
        general_limit: int = 120,   # Max general API requests per minute
    ):
        super().__init__(app)
        self.auth_limit = auth_limit
        self.detect_limit = detect_limit
        self.general_limit = general_limit
        self._lock = threading.Lock()
        # client_ip -> list of timestamps
        self._requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Bypass CORS preflight OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = time.time()
        window_seconds = 60.0

        # Determine path category & threshold
        if "/api/v1/auth/login" in path or "/api/v1/auth/register" in path:
            limit = self.auth_limit
            bucket_key = f"{client_ip}:auth"
        elif "/api/v1/detect" in path:
            limit = self.detect_limit
            bucket_key = f"{client_ip}:detect"
        else:
            limit = self.general_limit
            bucket_key = f"{client_ip}:general"

        with self._lock:
            # Clean expired timestamps outside the window
            timestamps = self._requests.get(bucket_key, [])
            valid_timestamps = [t for t in timestamps if now - t < window_seconds]

            if len(valid_timestamps) >= limit:
                retry_after = int(window_seconds - (now - valid_timestamps[0])) + 1
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "data": None,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Too many requests. Please wait {retry_after} seconds before trying again.",
                        },
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            valid_timestamps.append(now)
            self._requests[bucket_key] = valid_timestamps

            # Memory safeguard: periodically prune dead keys if bucket store grows large
            if len(self._requests) > 2000:
                self._requests = {
                    k: v for k, v in self._requests.items()
                    if v and (now - v[-1] < window_seconds)
                }

        return await call_next(request)


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
        return response


# ---------------------------------------------------------------------------
# Magic Byte & Image Sanitization Guard
# ---------------------------------------------------------------------------
_MAGIC_BYTES = {
    "jpeg": [b"\xFF\xD8\xFF"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "webp": [b"RIFF"],
    "bmp": [b"BM"],
}

def sanitize_and_verify_image(
    file_bytes: bytes,
    max_size_bytes: int = 10 * 1024 * 1024
) -> tuple[bool, str]:
    """
    Validates image binary content against file size limits, magic bytes,
    and structural integrity via PIL decoding.
    Returns (is_valid, error_message).
    """
    if not file_bytes:
        return False, "File is empty."

    if len(file_bytes) > max_size_bytes:
        return False, f"File exceeds maximum allowed size ({max_size_bytes // (1024*1024)}MB)."

    # Magic byte verification
    is_magic_valid = False
    for fmt, signatures in _MAGIC_BYTES.items():
        for sig in signatures:
            if file_bytes.startswith(sig):
                if fmt == "webp":
                    # WebP format has RIFF at start and WEBP at bytes 8-12
                    if len(file_bytes) >= 12 and file_bytes[8:12] == b"WEBP":
                        is_magic_valid = True
                        break
                else:
                    is_magic_valid = True
                    break
        if is_magic_valid:
            break

    if not is_magic_valid:
        return False, "Invalid image header signature. Only genuine JPEG, PNG, WebP, or BMP files are permitted."

    # Structural decoding verification
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
    except Exception:
        return False, "Corrupted or malformed image data."

    return True, ""


# ---------------------------------------------------------------------------
# Token Revocation / Blacklist Store
# ---------------------------------------------------------------------------
_REVOKED_TOKENS: set[str] = set()
_TOKEN_LOCK = threading.Lock()

def revoke_token(token: str) -> None:
    with _TOKEN_LOCK:
        _REVOKED_TOKENS.add(token)
    try:
        from server import db as sqlite_db
        sqlite_db.add_revoked_token(token, "")
    except Exception:
        pass

def is_token_revoked(token: str) -> bool:
    with _TOKEN_LOCK:
        if token in _REVOKED_TOKENS:
            return True
    try:
        from server import db as sqlite_db
        if sqlite_db.is_token_revoked_db(token):
            with _TOKEN_LOCK:
                _REVOKED_TOKENS.add(token)
            return True
    except Exception:
        pass
    return False
