"""
Unit tests for authentication
"""

import pytest
from fastapi import status
from auth import verify_password, get_password_hash, create_access_token, verify_token


@pytest.mark.unit
def test_password_hashing():
    """Test password hashing and verification"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


@pytest.mark.unit
def test_token_creation():
    """Test JWT token creation"""
    data = {"sub": "testuser", "user_id": 1}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.unit
def test_token_verification():
    """Test JWT token verification"""
    data = {"sub": "testuser", "user_id": 1}
    token = create_access_token(data)
    
    token_data = verify_token(token)
    assert token_data is not None
    assert token_data.username == "testuser"
    assert token_data.user_id == 1


@pytest.mark.unit
def test_token_verification_invalid():
    """Test invalid token verification"""
    token_data = verify_token("invalid.token.here")
    assert token_data is None

