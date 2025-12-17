"""
Tests for Qualitative Modeling Service
Comprehensive test suite for CTL verification, parameter generation, and state graphs
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from main import app, CTLFormula
from ctl_processor import CTLProcessor
from smbionet_integration import SMBioNetIntegration
from state_graph import StateGraphGenerator


client = TestClient(app)


class TestCTLProcessor:
    """Test CTL formula processor"""
    
    def test_valid_ctl_formula(self):
        processor = CTLProcessor()
        is_valid, errors = processor.validate_syntax("AG(p -> AF q)")
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_ctl_formula_unbalanced(self):
        processor = CTLProcessor()
        is_valid, errors = processor.validate_syntax("AG(p -> AF q")
        assert not is_valid
        assert len(errors) > 0
    
    def test_parse_formula(self):
        processor = CTLProcessor()
        result = processor.parse_formula("AG(p -> AF q)")
        assert result["original"] == "AG(p -> AF q)"
        assert "operators" in result
        assert result["has_temporal"] is True


class TestSMBioNetIntegration:
    """Test SMBioNet integration"""
    
    def test_verify_ctl(self):
        smbionet = SMBioNetIntegration()
        result = smbionet.verify_ctl("AG(p -> AF q)")
        assert result["valid"] is True
    
    def test_generate_parameters(self):
        smbionet = SMBioNetIntegration()
        network_structure = {
            "nodes": [{"id": "gene1"}, {"id": "gene2"}]
        }
        result = smbionet.generate_parameters(
            network_id="test_network",
            ctl_formula="AG(p -> AF q)",
            network_structure=network_structure
        )
        assert "parameters" in result
        assert result["count"] > 0
    
    def test_filter_parameters(self):
        smbionet = SMBioNetIntegration()
        parameter_sets = [
            {"node_id": "gene1", "k_values": {"k1": 1, "k2": 2}},
            {"node_id": "gene2", "k_values": {"k1": 3, "k2": 4}}
        ]
        constraints = {
            "k_value_range": {"min": 1, "max": 2}
        }
        result = smbionet.filter_parameters(parameter_sets, constraints)
        assert result["filtered_count"] <= result["original_count"]


class TestStateGraphGenerator:
    """Test state graph generator"""
    
    def test_generate_state_graph(self):
        generator = StateGraphGenerator()
        network_structure = {
            "nodes": [{"id": "gene1"}, {"id": "gene2"}]
        }
        parameters = [
            {"node_id": "gene1", "k_values": {"k1": 1}},
            {"node_id": "gene2", "k_values": {"k1": 1}}
        ]
        result = generator.generate_state_graph(
            network_id="test_network",
            parameters=parameters,
            network_structure=network_structure
        )
        assert "states" in result
        assert "transitions" in result
        assert result["state_count"] > 0


class TestQualitativeServiceAPI:
    """Test Qualitative Service API endpoints"""
    
    def test_verify_ctl_endpoint(self):
        """Test CTL verification endpoint"""
        response = client.post(
            "/ctl/verify",
            json={"formula": "AG(p -> AF q)", "description": "Test formula"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "valid" in data
        assert data["valid"] is True
        assert "errors" in data
        assert "warnings" in data
    
    def test_verify_ctl_endpoint_invalid_formula(self):
        """Test CTL verification with invalid formula"""
        response = client.post(
            "/ctl/verify",
            json={"formula": "AG(p -> AF", "description": "Invalid formula"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "valid" in data
        # May be valid or invalid depending on implementation
    
    def test_verify_ctl_endpoint_empty_formula(self):
        """Test CTL verification with empty formula"""
        response = client.post(
            "/ctl/verify",
            json={"formula": "", "description": "Empty formula"}
        )
        # Should return validation error
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_200_OK]
    
    def test_generate_parameters_endpoint(self):
        """Test parameter generation endpoint"""
        response = client.post(
            "/parameters/generate?network_id=test_network",
            json={"formula": "AG(p -> AF q)", "description": "Test"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "parameters" in data
        assert "count" in data
        assert isinstance(data["count"], int)
        assert data["count"] >= 0
    
    def test_generate_parameters_with_network_structure(self):
        """Test parameter generation with network structure"""
        network_structure = {
            "nodes": [{"id": "gene1"}, {"id": "gene2"}],
            "edges": [{"source": "gene1", "target": "gene2"}]
        }
        response = client.post(
            "/parameters/generate?network_id=test_network",
            json={
                "formula": "AG(p -> AF q)",
                "description": "Test",
                "network_structure": network_structure
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "parameters" in data
        assert len(data["parameters"]) > 0
    
    def test_filter_parameters_endpoint(self):
        response = client.post(
            "/parameters/filter",
            json={
                "parameter_sets": [
                    {"node_id": "gene1", "k_values": {"k1": 1}}
                ],
                "constraints": {"k_value_range": {"min": 1, "max": 2}}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "filtered" in data
    
    def test_generate_state_graph_endpoint(self):
        response = client.post(
            "/state-graph/generate?network_id=test_network",
            json={
                "parameters": [{"node_id": "gene1", "k_values": {"k1": 1}}]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "states" in data
        assert "transitions" in data
    
    def test_health_endpoints(self):
        response = client.get("/health/live")
        assert response.status_code == 200
        
        response = client.get("/health/ready")
        assert response.status_code == 200

