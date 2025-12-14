"""
Performance and load tests
"""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


@pytest.mark.slow
class TestLoadPerformance:
    """Load testing for API endpoints"""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for load tests"""
        response = requests.post(
            f"{self.BASE_URL}/api/v1/auth/token",
            data={"username": "testuser", "password": "testpass"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    def test_concurrent_requests(self, auth_token):
        """Test handling concurrent requests"""
        if not auth_token:
            pytest.skip("Auth token not available")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        num_requests = 50
        
        def make_request():
            response = requests.get(
                f"{self.BASE_URL}/api/v1/networks",
                headers=headers,
                timeout=5
            )
            return response.status_code
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [f.result() for f in as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check all requests succeeded
        success_rate = sum(1 for r in results if r == 200) / len(results)
        
        assert success_rate >= 0.95, f"Success rate too low: {success_rate}"
        assert duration < 30, f"Too slow: {duration}s for {num_requests} requests"
        
        print(f"Processed {num_requests} requests in {duration:.2f}s")
        print(f"Success rate: {success_rate * 100:.1f}%")
    
    def test_response_time(self, auth_token):
        """Test response time for health check"""
        response = requests.get(f"{self.BASE_URL}/api/v1/auth/health")
        
        assert response.elapsed.total_seconds() < 1.0
        assert response.status_code == 200

