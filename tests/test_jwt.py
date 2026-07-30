"""JWT token tests."""

from datetime import timedelta

import pytest
from jose import JWTError

from app.security.jwt import create_access_token, create_refresh_token, decode_token


def test_create_and_decode_access_token():
    token, jti, exp = create_access_token(
        user_id=1,
        username="admin",
        roles=["SUPER_ADMIN"],
        permissions=["auth.admin.full"],
        session_id="test-session-id",
    )
    assert token
    assert jti
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["username"] == "admin"
    assert payload["type"] == "access"
    assert "SUPER_ADMIN" in payload["roles"]


def test_create_and_decode_refresh_token():
    token, jti, exp = create_refresh_token(user_id=1, session_id="test-session", remember_me=False)
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    assert payload["sub"] == "1"


def test_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_token("invalid.token.here")
