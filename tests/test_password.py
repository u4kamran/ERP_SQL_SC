"""Password policy validation tests."""

import pytest

from app.security.password import hash_password, validate_password_policy, verify_password


def test_hash_and_verify_password():
    password = "SecurePass@123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_password_policy_valid():
    valid, errors = validate_password_policy("SecurePass@123")
    assert valid is True
    assert len(errors) == 0


def test_password_policy_too_short():
    valid, errors = validate_password_policy("Ab@1")
    assert valid is False
    assert any("at least" in e for e in errors)


def test_password_policy_missing_uppercase():
    valid, errors = validate_password_policy("securepass@123")
    assert valid is False
    assert any("uppercase" in e for e in errors)
