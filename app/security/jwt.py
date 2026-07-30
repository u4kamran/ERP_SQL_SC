"""JWT token creation and validation."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from app.config.settings import settings


def create_access_token(
    user_id: int,
    username: str,
    roles: list[str],
    permissions: list[str],
    session_id: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str, datetime]:
    """Create JWT access token. Returns (token, jti, expires_at)."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )

    payload = {
        "sub": str(user_id),
        "username": username,
        "roles": roles,
        "permissions": permissions,
        "session_id": session_id,
        "type": "access",
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expire


def create_refresh_token(
    user_id: int,
    session_id: str,
    remember_me: bool = False,
) -> tuple[str, str, datetime]:
    """Create JWT refresh token. Returns (token, jti, expires_at)."""
    jti = str(uuid.uuid4())
    days = settings.jwt_remember_me_expire_days if remember_me else settings.jwt_refresh_token_expire_days
    expire = datetime.now(timezone.utc) + timedelta(days=days)

    payload = {
        "sub": str(user_id),
        "session_id": session_id,
        "type": "refresh",
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expire


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
