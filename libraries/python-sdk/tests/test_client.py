"""
Tests for Python SDK client
"""

import pytest
from unittest.mock import Mock, patch
import requests
from gennet.client import GenNetClient


@pytest.mark.unit
def test_client_initialization():
    """Test client initialization"""
    client = GenNetClient(base_url="http://localhost:8000")
    assert client.base_url == "http://localhost:8000"


@pytest.mark.unit
def test_client_with_api_key():
    """Test client with API key"""
    client = GenNetClient(base_url="http://localhost:8000", api_key="test-key")
    assert "Authorization" in client.session.headers
    assert client.session.headers["Authorization"] == "Bearer test-key"


@pytest.mark.unit
@patch('gennet.client.requests.Session')
def test_list_networks(mock_session):
    """Test listing networks"""
    mock_response = Mock()
    mock_response.json.return_value = [{"id": "net1", "name": "Network 1"}]
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.request.return_value = mock_response
    mock_session.return_value = mock_session_instance
    
    client = GenNetClient(base_url="http://localhost:8000")
    client.session = mock_session_instance
    
    networks = client.list_networks()
    assert len(networks) == 1
    assert networks[0]["id"] == "net1"


@pytest.mark.unit
@patch('gennet.client.requests.Session')
def test_create_workflow(mock_session):
    """Test creating a workflow"""
    mock_response = Mock()
    mock_response.json.return_value = {"id": "wf1", "name": "Workflow 1"}
    mock_response.raise_for_status = Mock()
    
    mock_session_instance = Mock()
    mock_session_instance.request.return_value = mock_response
    mock_session.return_value = mock_session_instance
    
    client = GenNetClient(base_url="http://localhost:8000")
    client.session = mock_session_instance
    
    workflow = client.create_workflow(
        name="Test Workflow",
        workflow_type="qualitative",
        network_id="net1"
    )
    
    assert workflow["id"] == "wf1"

