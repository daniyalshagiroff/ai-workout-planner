"""
Security utilities: password hashing (PBKDF2) and cookie signing for auth.
"""

import os
import hmac
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Tuple, Optional


def _get_secret() -> bytes:
    secret = os.environ.get("APP_SECRET_KEY") or "dev-secret-change-me"
    return secret.encode("utf-8")


def hash_password(password: str, iterations: int = 200_000) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations_s, salt_b64, hash_b64 = stored.split("$")
        iterations = int(iterations_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def sign_token(user_id: int, days_valid: int = 7) -> str:
    exp = int((datetime.utcnow() + timedelta(days=days_valid)).timestamp())
    payload = f"{user_id}.{exp}".encode("utf-8")
    sig = hmac.new(_get_secret(), payload, hashlib.sha256).digest()
    return f"{user_id}.{exp}.{base64.urlsafe_b64encode(sig).decode()}"


def verify_token(token: str) -> Optional[int]:
    try:
        user_id_s, exp_s, sig_b64 = token.split(".")
        exp = int(exp_s)
        if int(datetime.utcnow().timestamp()) > exp:
            return None
        payload = f"{user_id_s}.{exp_s}".encode("utf-8")
        expected_sig = hmac.new(_get_secret(), payload, hashlib.sha256).digest()
        sig = base64.urlsafe_b64decode(sig_b64.encode())
        if not hmac.compare_digest(sig, expected_sig):
            return None
        return int(user_id_s)
    except Exception:
        return None


