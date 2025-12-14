"""
Pytest fixtures for workflow service tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock

from main import app
from models import Base, Workflow, JobStatus
from database import get_db
from workflow_engine import WorkflowEngine

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_workflow.db"
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
def mock_workflow_engine():
    """Mock workflow engine"""
    return Mock(spec=WorkflowEngine)


@pytest.fixture(scope="function")
def client(db, mock_workflow_engine):
    """Create test client"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    app.workflow_engine = mock_workflow_engine
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_workflow(db):
    """Create a test workflow"""
    workflow = Workflow(
        id="test-workflow-1",
        name="Test Workflow",
        workflow_type="qualitative",
        network_id="test-network-1",
        status=JobStatus.PENDING,
        owner_id=1
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow

