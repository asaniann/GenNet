"""
Integration Tests for Qualitative Service
Tests service-to-service communication and end-to-end workflows
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestQualitativeWorkflow:
    """Test complete qualitative modeling workflow"""
    
    def test_complete_workflow(self):
        """Test complete workflow: verify -> generate -> filter -> state graph"""
        # Step 1: Verify CTL formula
        verify_response = client.post(
            "/ctl/verify",
            json={"formula": "AG(p -> AF q)", "description": "Test workflow"}
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["valid"] is True
        
        # Step 2: Generate parameters
        network_structure = {
            "nodes": [{"id": "gene1"}, {"id": "gene2"}],
            "edges": [{"source": "gene1", "target": "gene2"}]
        }
        params_response = client.post(
            "/parameters/generate?network_id=test_workflow",
            json={
                "formula": "AG(p -> AF q)",
                "description": "Test",
                "network_structure": network_structure
            }
        )
        assert params_response.status_code == 200
        params_data = params_response.json()
        assert "parameters" in params_data
        
        # Step 3: Filter parameters
        filter_response = client.post(
            "/parameters/filter",
            json={
                "parameter_sets": params_data["parameters"],
                "constraints": {"k_value_range": {"min": 1, "max": 3}}
            }
        )
        assert filter_response.status_code == 200
        filter_data = filter_response.json()
        assert "filtered" in filter_data
        
        # Step 4: Generate state graph
        state_graph_response = client.post(
            "/state-graph/generate?network_id=test_workflow",
            json={
                "parameters": filter_data["filtered"],
                "network_structure": network_structure
            }
        )
        assert state_graph_response.status_code == 200
        state_graph_data = state_graph_response.json()
        assert "states" in state_graph_data
        assert "transitions" in state_graph_data

