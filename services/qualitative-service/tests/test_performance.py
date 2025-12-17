"""
Performance Tests for Qualitative Service
Tests performance characteristics and optimization
"""

import pytest
import time
from fastapi.testclient import TestClient
from main import app
from ctl_processor import CTLProcessor
from smbionet_integration import SMBioNetIntegration

client = TestClient(app)


class TestPerformance:
    """Performance tests"""
    
    def test_ctl_verification_performance(self):
        """Test CTL verification performance"""
        processor = CTLProcessor()
        
        # Test with various formula complexities
        formulas = [
            "AG(p -> AF q)",
            "AG(p -> AF(q AND r))",
            "AG((p -> AF q) AND (r -> EF s))",
            "AG((p -> AF(q AND r)) OR (s -> EG t))"
        ]
        
        for formula in formulas:
            start = time.time()
            is_valid, errors = processor.validate_syntax(formula)
            elapsed = time.time() - start
            
            # Should complete in reasonable time (< 1 second)
            assert elapsed < 1.0, f"CTL verification took {elapsed:.2f}s for {formula}"
            assert isinstance(is_valid, bool)
    
    def test_parameter_generation_performance(self):
        """Test parameter generation performance"""
        smbionet = SMBioNetIntegration()
        
        # Test with different network sizes
        network_sizes = [5, 10, 20, 50]
        
        for size in network_sizes:
            network_structure = {
                "nodes": [{"id": f"gene{i}"} for i in range(size)]
            }
            
            start = time.time()
            result = smbionet.generate_parameters(
                network_id=f"test_network_{size}",
                ctl_formula="AG(p -> AF q)",
                network_structure=network_structure
            )
            elapsed = time.time() - start
            
            # Should scale reasonably
            assert elapsed < 5.0, f"Parameter generation took {elapsed:.2f}s for {size} nodes"
            assert "parameters" in result
            assert result["count"] > 0
    
    def test_api_response_time(self):
        """Test API endpoint response times"""
        endpoints = [
            ("/health/live", "GET"),
            ("/health/ready", "GET"),
            ("/ctl/verify", "POST", {"formula": "AG(p -> AF q)"})
        ]
        
        for endpoint_info in endpoints:
            endpoint = endpoint_info[0]
            method = endpoint_info[1]
            data = endpoint_info[2] if len(endpoint_info) > 2 else None
            
            start = time.time()
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=data)
            elapsed = time.time() - start
            
            # API should respond quickly (< 500ms for health, < 2s for processing)
            max_time = 0.5 if "health" in endpoint else 2.0
            assert elapsed < max_time, f"{endpoint} took {elapsed:.2f}s"
            assert response.status_code in [200, 401, 422]  # Acceptable status codes

