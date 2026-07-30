"""CSRF token generation and validation."""

import secrets

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config.settings import settings

_serializer = URLSafeTimedSerializer(settings.csrf_secret_key)


def generate_csrf_token() -> str:
    return _serializer.dumps(secrets.token_hex(32))


def validate_csrf_token(token: str, max_age: int = 3600) -> bool:
    try:
        _serializer.loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False
