"""
Tests for workflow engine
"""

import pytest
from unittest.mock import Mock, patch
from models import Workflow, JobStatus
from workflow_engine import WorkflowEngine
from database import SessionLocal, engine
from models import Base


@pytest.mark.unit
def test_workflow_engine_initialization():
    """Test workflow engine initialization"""
    engine = WorkflowEngine()
    assert engine is not None


@pytest.mark.unit
@patch('workflow_engine.SessionLocal')
def test_execute_workflow(mock_session_local):
    """Test workflow execution"""
    mock_db = Mock()
    mock_workflow = Mock(spec=Workflow)
    mock_workflow.id = "test-workflow"
    mock_workflow.workflow_type = "qualitative"
    mock_workflow.status = JobStatus.PENDING
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_workflow
    
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = None
    
    workflow_engine = WorkflowEngine()
    workflow_engine._execute_qualitative_workflow = Mock()
    
    workflow_engine.execute_workflow("test-workflow")
    
    assert mock_db.commit.called

