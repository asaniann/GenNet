"""
Shared test fixtures for all services
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///./test.db"
)


@pytest.fixture
def test_db():
    """Create test database session"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up test database
        if TEST_DATABASE_URL.startswith("sqlite"):
            os.remove("./test.db")


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing"""
    return "mock_jwt_token_for_testing"


@pytest.fixture
def mock_user_id():
    """Mock user ID for testing"""
    return 1


@pytest.fixture
def mock_patient_id():
    """Mock patient ID for testing"""
    return "test-patient-123"


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "anonymized_id": "PAT-001",
        "age_range": "40-50",
        "gender": "F",
        "has_genomic_data": True,
        "has_expression_data": True,
        "consent_given": True
    }


@pytest.fixture
def sample_expression_data():
    """Sample expression data for testing"""
    import pandas as pd
    import numpy as np
    
    return pd.DataFrame({
        "GENE1": np.random.randn(100),
        "GENE2": np.random.randn(100),
        "GENE3": np.random.randn(100)
    })


@pytest.fixture
def sample_genomic_data():
    """Sample genomic data for testing"""
    return {
        "variants": [
            {"chrom": "1", "pos": 1000, "ref": "A", "alt": "G", "gene": "GENE1"},
            {"chrom": "2", "pos": 2000, "ref": "C", "alt": "T", "gene": "GENE2"}
        ],
        "prs_scores": {
            "disease_1": 65.5,
            "disease_2": 45.2
        }
    }

