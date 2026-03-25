"""HS256 JWT — no third-party dependency required."""
import base64
import hashlib
import hmac
import json
import time

from app.config import Config


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def _b64d(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)

def _sign(msg: str) -> str:
    return _b64e(
        hmac.new(Config.JWT_SECRET.encode(), msg.encode(), hashlib.sha256).digest()
    )

def create_token(account_id: str, duid: str, role: str) -> tuple[str, int]:
    hdr = _b64e(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    now = int(time.time())
    pay = _b64e(json.dumps({
        "sub":  account_id,
        "duid": duid,
        "role": role,
        "iat":  now,
        "exp":  now + Config.JWT_EXPIRY_SEC,
    }).encode())
    sig = _sign(f"{hdr}.{pay}")
    return f"{hdr}.{pay}.{sig}", Config.JWT_EXPIRY_SEC

def decode_token(token: str) -> dict | None:
    try:
        h, p, s = token.split(".")
        if not hmac.compare_digest(_sign(f"{h}.{p}"), s):
            return None
        payload = json.loads(_b64d(p))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None
