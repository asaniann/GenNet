"""
API endpoint tests for auth service
"""

import pytest
from fastapi import status


@pytest.mark.integration
def test_register_user(client):
    """Test user registration"""
    response = client.post(
        "/register",
        params={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "user_id" in data
    assert data["message"] == "User created successfully"


@pytest.mark.integration
def test_register_duplicate_username(client, test_user):
    """Test registration with duplicate username"""
    response = client.post(
        "/register",
        params={
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.integration
def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post(
        "/token",
        data={
            "username": test_user.username,
            "password": "testpass123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.integration
def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials"""
    response = client.post(
        "/token",
        data={
            "username": test_user.username,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
def test_get_current_user(client, auth_token):
    """Test getting current user info"""
    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "username" in data
    assert "email" in data
    assert data["username"] == "testuser"


@pytest.mark.integration
def test_get_current_user_no_auth(client):
    """Test getting user info without auth"""
    response = client.get("/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
def test_logout(client, auth_token):
    """Test logout"""
    response = client.post(
        "/logout",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Logged out successfully"


@pytest.mark.integration
def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"

