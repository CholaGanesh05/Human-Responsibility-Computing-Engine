"""
tests/test_auth.py — Unit tests for Stage 11: Security & Auth

Tests cover:
  1. JWT token creation and decoding (round-trip)
  2. Invalid JWT token returns None from decode_access_token  
  3. hash_password + verify_password logic (mocked to avoid passlib/bcrypt compat issues on Python 3.14)
  4. register() hashes password and creates a valid token
  5. Wrong password check fails verification (login 401 logic)
"""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import timedelta


# ──────────────────────────────────────────────────────────────────────────────
# Test 1: JWT round-trip
# ──────────────────────────────────────────────────────────────────────────────

def test_create_and_decode_access_token():
    """Token can be created and decoded; sub matches original user_id."""
    from app.core.security import create_access_token, decode_access_token

    user_id = str(uuid4())
    token = create_access_token(data={"sub": user_id}, expires_delta=timedelta(minutes=30))

    assert isinstance(token, str), "Token must be a string"
    assert token.count(".") == 2, "JWT must have 3 parts separated by dots"

    payload = decode_access_token(token)
    assert payload is not None, "decode_access_token should return payload for a valid token"
    assert payload["sub"] == user_id, "Decoded 'sub' must match the original user id"


# ──────────────────────────────────────────────────────────────────────────────
# Test 2: Invalid token decodes to None
# ──────────────────────────────────────────────────────────────────────────────

def test_decode_invalid_token_returns_none():
    """decode_access_token should return None for a tampered or garbage token."""
    from app.core.security import decode_access_token

    result = decode_access_token("this.is.not.a.valid.jwt")
    assert result is None

    result2 = decode_access_token("eyJ.bad.sig")
    assert result2 is None


# ──────────────────────────────────────────────────────────────────────────────
# Test 3: hash_password and verify_password (mocked CryptContext)
# ──────────────────────────────────────────────────────────────────────────────

def test_hash_and_verify_password_logic():
    """
    Tests the hash_password / verify_password wiring with a mocked CryptContext
    to avoid passlib bcrypt compat issues on Python 3.14.
    The real bcrypt hashing is verified inside Docker where passlib is fully supported.
    """
    # Mock the CryptContext so we test the function wiring without calling bcrypt
    mock_context = MagicMock()
    mock_context.hash.return_value = "hashed_secret"
    mock_context.verify.side_effect = lambda plain, hashed: plain == "secret" and hashed == "hashed_secret"

    with patch("app.core.security._pwd_context", mock_context):
        from app.core import security

        result_hash = security.hash_password("secret")
        assert result_hash == "hashed_secret"
        mock_context.hash.assert_called_once_with("secret")

        assert security.verify_password("secret", "hashed_secret") is True
        assert security.verify_password("wrong", "hashed_secret") is False


# ──────────────────────────────────────────────────────────────────────────────
# Test 4: register logic — hash + token creation
# ──────────────────────────────────────────────────────────────────────────────

def test_register_creates_token_with_user_id():
    """
    Simulates the register endpoint logic using mocked hashing.
    Verifies that a token is returned with the correct sub claim.
    """
    from app.core.security import create_access_token, decode_access_token

    mock_context = MagicMock()
    mock_context.hash.return_value = "bcrypt_hashed_pw"

    with patch("app.core.security._pwd_context", mock_context):
        from app.core import security

        hashed = security.hash_password("my_password")
        assert hashed == "bcrypt_hashed_pw"

    # Token creation doesn't depend on bcrypt at all
    fake_user_id = str(uuid4())
    token = create_access_token(data={"sub": fake_user_id})
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == fake_user_id


# ──────────────────────────────────────────────────────────────────────────────
# Test 5: Wrong password → verify_password returns False (login 401 logic)
# ──────────────────────────────────────────────────────────────────────────────

def test_wrong_password_fails_verification():
    """
    Simulates the login endpoint's credential check with mocked bcrypt.
    verify_password must return False for a wrong password → endpoint raises 401.
    """
    mock_context = MagicMock()
    # Simulate: only "correct_password" matches the stored hash
    mock_context.verify.side_effect = lambda plain, hashed: plain == "correct_password"

    with patch("app.core.security._pwd_context", mock_context):
        from app.core import security

        assert security.verify_password("WRONG_PASSWORD", "stored_hash") is False
        assert security.verify_password("correct_password", "stored_hash") is True
