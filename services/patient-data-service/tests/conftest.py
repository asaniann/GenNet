"""
Pytest configuration and fixtures for Patient Data Service tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app
from database import get_db, Base
from models import Patient


# Test database (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_patient_data():
    """Sample patient data for testing"""
    return {
        "user_id": 1,
        "age_range": "40-50",
        "gender": "M",
        "ethnicity": "EUR",
        "consent_given": True,
        "data_retention_policy": "standard"
    }


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing"""
    import jwt
    import os
    
    secret = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    token = jwt.encode({"sub": 1}, secret, algorithm="HS256")
    return token

