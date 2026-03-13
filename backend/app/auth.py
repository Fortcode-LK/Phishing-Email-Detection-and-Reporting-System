# backend/app/auth.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = "super-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7

_bearer = HTTPBearer(auto_error=True)


def create_token(user_id: int, email: str, role: str = "normal") -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": datetime.now(tz=timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.now(tz=timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Token has expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid token"},
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """FastAPI dependency — returns {"user_id": int, "email": str}."""
    payload = decode_token(credentials.credentials)
    return {
        "user_id": int(payload["sub"]),
        "email": payload.get("email", ""),
        "role": payload.get("role", "normal"),
    }
