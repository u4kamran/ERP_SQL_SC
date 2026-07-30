"""Password hashing and policy validation using BCrypt."""

import re
from typing import List, Tuple

import bcrypt

from app.config.settings import settings


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def validate_password_policy(password: str) -> Tuple[bool, List[str]]:
    """Validate password against configured policy. Returns (is_valid, error_messages)."""
    errors: List[str] = []

    if len(password) < settings.password_min_length:
        errors.append(f"Password must be at least {settings.password_min_length} characters.")

    if settings.password_require_uppercase and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")

    if settings.password_require_lowercase and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")

    if settings.password_require_digit and not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")

    if settings.password_require_special and not re.search(
        r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;/'`~]", password
    ):
        errors.append("Password must contain at least one special character.")

    return len(errors) == 0, errors
