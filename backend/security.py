"""Password hashing (stdlib PBKDF2, no native deps) and JWT issuing/verification."""
import base64
import hashlib
import hmac
import os
import time

import jwt

from config import JWT_SECRET, JWT_EXPIRES_MINUTES

PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return base64.b64encode(salt + derived).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    try:
        raw = base64.b64decode(hashed.encode("ascii"))
    except Exception:
        return False
    salt, expected = raw[:16], raw[16:]
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(derived, expected)


def create_access_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "iat": int(time.time()), "exp": int(time.time()) + JWT_EXPIRES_MINUTES * 60}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return int(payload["sub"])
    except Exception:
        return None
