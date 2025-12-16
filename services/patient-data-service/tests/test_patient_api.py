"""
Tests for Patient Data Service API endpoints
"""

import pytest
from fastapi import status
from models import Patient
from datetime import datetime


def test_create_patient(client, db_session, test_patient_data, mock_jwt_token):
    """Test creating a new patient"""
    response = client.post(
        "/patients",
        json=test_patient_data,
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_id"] == test_patient_data["user_id"]
    assert data["anonymized_id"].startswith("PAT-")
    assert data["consent_given"] == True
    assert "id" in data
    assert "created_at" in data


def test_list_patients(client, db_session, test_patient_data, mock_jwt_token):
    """Test listing patients"""
    # Create a patient first
    client.post(
        "/patients",
        json=test_patient_data,
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # List patients
    response = client.get(
        "/patients",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_patient(client, db_session, test_patient_data, mock_jwt_token):
    """Test getting a specific patient"""
    # Create a patient
    create_response = client.post(
        "/patients",
        json=test_patient_data,
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    patient_id = create_response.json()["id"]
    
    # Get the patient
    response = client.get(
        f"/patients/{patient_id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == patient_id
    assert data["user_id"] == test_patient_data["user_id"]


def test_update_patient(client, db_session, test_patient_data, mock_jwt_token):
    """Test updating a patient"""
    # Create a patient
    create_response = client.post(
        "/patients",
        json=test_patient_data,
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    patient_id = create_response.json()["id"]
    
    # Update the patient
    update_data = {"age_range": "50-60", "gender": "F"}
    response = client.put(
        f"/patients/{patient_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["age_range"] == "50-60"
    assert data["gender"] == "F"


def test_delete_patient(client, db_session, test_patient_data, mock_jwt_token):
    """Test soft deleting a patient"""
    # Create a patient
    create_response = client.post(
        "/patients",
        json=test_patient_data,
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    patient_id = create_response.json()["id"]
    
    # Delete the patient (soft delete)
    response = client.delete(
        f"/patients/{patient_id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify patient is soft-deleted (should not appear in list)
    list_response = client.get(
        "/patients",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    patient_ids = [p["id"] for p in list_response.json()]
    assert patient_id not in patient_ids


def test_health_endpoints(client):
    """Test health check endpoints"""
    # Liveness
    response = client.get("/health/live")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "alive"
    
    # Readiness
    response = client.get("/health/ready")
    assert response.status_code in [200, 503]  # May be 503 if DB not available


def test_patient_access_control(client, db_session, test_patient_data):
    """Test that users can only access their own patients"""
    import jwt
    import os
    
    # Create patient with user_id 1
    token1 = jwt.encode({"sub": 1}, os.getenv("JWT_SECRET_KEY", "dev-secret-key"), algorithm="HS256")
    create_response = client.post(
        "/patients",
        json=test_patient_data,
        headers={"Authorization": f"Bearer {token1}"}
    )
    patient_id = create_response.json()["id"]
    
    # Try to access with different user (user_id 2)
    token2 = jwt.encode({"sub": 2}, os.getenv("JWT_SECRET_KEY", "dev-secret-key"), algorithm="HS256")
    response = client.get(
        f"/patients/{patient_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    # Should return 404 (not found) due to access control
    assert response.status_code == status.HTTP_404_NOT_FOUND

