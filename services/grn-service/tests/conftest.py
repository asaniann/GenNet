"""
Pytest fixtures for GRN service tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, MagicMock

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from models import Base, GRNNetwork
from database import get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_grn.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def mock_neo4j():
    """Mock Neo4j client"""
    mock = Mock()
    mock.get_network.return_value = {"nodes": [], "edges": []}
    mock.get_subgraph.return_value = {"nodes": [], "edges": []}
    mock.create_network = Mock()
    mock.update_network = Mock()
    mock.delete_network = Mock()
    return mock


@pytest.fixture(scope="function")
def mock_s3():
    """Mock S3 client"""
    return Mock()


@pytest.fixture(scope="function")
def client(db, mock_neo4j, mock_s3):
    """Create test client"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    # Mock dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.neo4j_client = mock_neo4j
    app.s3_client = mock_s3
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_network(db):
    """Create a test network"""
    network = GRNNetwork(
        id="test-network-1",
        name="Test Network",
        description="A test network",
        owner_id=1
    )
    db.add(network)
    db.commit()
    db.refresh(network)
    return network


@pytest.fixture
def auth_headers():
    """Mock auth headers"""
    return {"Authorization": "Bearer test-token"}

