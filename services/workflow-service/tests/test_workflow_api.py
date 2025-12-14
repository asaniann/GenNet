"""
API tests for workflow service
"""

import pytest
from fastapi import status


@pytest.mark.integration
def test_create_workflow(client):
    """Test creating a workflow"""
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "workflow_type": "qualitative",
        "network_id": "test-network-1",
        "parameters": {}
    }
    
    response = client.post("/workflows", json=workflow_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["name"] == workflow_data["name"]


@pytest.mark.integration
def test_list_workflows(client, test_workflow):
    """Test listing workflows"""
    response = client.get("/workflows")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.integration
def test_get_workflow(client, test_workflow):
    """Test getting a workflow"""
    response = client.get(f"/workflows/{test_workflow.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_workflow.id


@pytest.mark.integration
def test_get_workflow_status(client, test_workflow):
    """Test getting workflow status"""
    response = client.get(f"/workflows/{test_workflow.id}/status")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data


@pytest.mark.integration
def test_get_workflow_results_not_completed(client, test_workflow):
    """Test getting results for non-completed workflow"""
    response = client.get(f"/workflows/{test_workflow.id}/results")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

