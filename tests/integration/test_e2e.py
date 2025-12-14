"""
End-to-end integration tests
"""

import pytest
import requests
import time
from typing import Dict


@pytest.mark.e2e
@pytest.mark.slow
class TestE2EWorkflow:
    """End-to-end workflow tests"""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture
    def auth_token(self) -> str:
        """Get authentication token"""
        # Register user
        response = requests.post(
            f"{self.BASE_URL}/api/v1/auth/register",
            params={
                "username": "e2e_test_user",
                "email": "e2e@test.com",
                "password": "testpass123"
            }
        )
        
        # Login
        response = requests.post(
            f"{self.BASE_URL}/api/v1/auth/token",
            data={
                "username": "e2e_test_user",
                "password": "testpass123"
            }
        )
        return response.json()["access_token"]
    
    def test_create_network_and_workflow(self, auth_token: str):
        """Test creating a network and running a workflow"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create network
        network_data = {
            "name": "E2E Test Network",
            "description": "Test network for E2E testing",
            "nodes": [
                {"id": "gene1", "label": "Gene 1", "node_type": "gene"},
                {"id": "gene2", "label": "Gene 2", "node_type": "gene"}
            ],
            "edges": [
                {"source": "gene1", "target": "gene2", "edge_type": "activates"}
            ]
        }
        
        network_response = requests.post(
            f"{self.BASE_URL}/api/v1/networks",
            json=network_data,
            headers=headers
        )
        assert network_response.status_code == 201
        network_id = network_response.json()["id"]
        
        # Create workflow
        workflow_data = {
            "name": "E2E Test Workflow",
            "workflow_type": "qualitative",
            "network_id": network_id,
            "parameters": {}
        }
        
        workflow_response = requests.post(
            f"{self.BASE_URL}/api/v1/workflows",
            json=workflow_data,
            headers=headers
        )
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["id"]
        
        # Check workflow status
        max_attempts = 30
        for _ in range(max_attempts):
            status_response = requests.get(
                f"{self.BASE_URL}/api/v1/workflows/{workflow_id}/status",
                headers=headers
            )
            status = status_response.json()["status"]
            
            if status in ["completed", "failed"]:
                break
            
            time.sleep(1)
        
        assert status in ["completed", "failed"]

