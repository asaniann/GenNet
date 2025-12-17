"""
Tests for Hybrid Modeling Service
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from hytech_integration import HyTechIntegration


client = TestClient(app)


class TestHyTechIntegration:
    """Test HyTech integration"""
    
    def test_compute_time_delays(self):
        hytech = HyTechIntegration()
        network_structure = {
            "nodes": [{"id": "node1"}, {"id": "node2"}]
        }
        result = hytech.compute_time_delays(
            network_id="test_network",
            parameters={"node1": {"rate": 0.1}},
            time_constraints={"node1_to_node2": 2.0},
            network_structure=network_structure
        )
        assert "delays" in result
        assert result["count"] > 0
    
    def test_analyze_trajectory(self):
        hytech = HyTechIntegration()
        network_structure = {
            "nodes": [{"id": "node1"}, {"id": "node2"}]
        }
        result = hytech.analyze_trajectory(
            network_id="test_network",
            parameters={"node1": {"rate": 0.1, "target": 1.0}},
            initial_state={"node1": 0.0, "node2": 0.0},
            time_horizon=5.0,
            time_step=0.1,
            network_structure=network_structure
        )
        assert "trajectory" in result
        assert result["point_count"] > 0
        assert "analysis" in result


class TestHybridServiceAPI:
    """Test Hybrid Service API endpoints"""
    
    def test_compute_time_delays_endpoint(self):
        response = client.post(
            "/time-delays/compute",
            json={
                "network_id": "test_network",
                "parameters": {"node1": {"rate": 0.1}},
                "time_constraints": {"node1_to_node2": 2.0}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "delays" in data
    
    def test_analyze_trajectory_endpoint(self):
        response = client.post(
            "/trajectory/analyze",
            json={
                "network_id": "test_network",
                "parameters": {"node1": {"rate": 0.1}},
                "time_constraints": {},
                "initial_state": {"node1": 0.0},
                "time_horizon": 5.0,
                "time_step": 0.1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "trajectory" in data
    
    def test_health_endpoints(self):
        response = client.get("/health/live")
        assert response.status_code == 200
        
        response = client.get("/health/ready")
        assert response.status_code == 200

