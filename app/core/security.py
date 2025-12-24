import time
import hmac
import base64
import hashlib
import json
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from app.core.config import settings

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_jwt(sub: str, extra: Optional[Dict[str, Any]] = None) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload: Dict[str, Any] = {
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "sub": sub,
        "iat": now,
        "exp": now + int(settings.JWT_EXPIRES_MINUTES) * 60,
    }
    if extra:
        payload.update(extra)

    signing_input = f"{_b64url_encode(json.dumps(header).encode())}.{_b64url_encode(json.dumps(payload).encode())}"
    signature = hmac.new(settings.JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"

def verify_jwt(token: str) -> Dict[str, Any]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("invalid token format")

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}"
        expected = hmac.new(settings.JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()

        if not hmac.compare_digest(_b64url_decode(sig_b64), expected):
            raise ValueError("invalid signature")

        payload = json.loads(_b64url_decode(payload_b64))
        now = int(time.time())

        if payload.get("iss") != settings.JWT_ISSUER:
            raise ValueError("invalid iss")
        if payload.get("aud") != settings.JWT_AUDIENCE:
            raise ValueError("invalid aud")
        if now >= int(payload.get("exp", 0)):
            raise ValueError("expired")

        return payload
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
