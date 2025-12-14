"""GenNet API Client"""

import requests
from typing import Optional, Dict, Any, List


class GenNetClient:
    """Client for interacting with GenNet API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    
    def list_networks(self) -> List[Dict[str, Any]]:
        """List all networks"""
        response = self._request('GET', '/api/v1/networks')
        return response.json()
    
    def get_network(self, network_id: str) -> Dict[str, Any]:
        """Get a specific network"""
        response = self._request('GET', f'/api/v1/networks/{network_id}')
        return response.json()
    
    def create_network(self, name: str, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """Create a new network"""
        data = {
            "name": name,
            "nodes": nodes,
            "edges": edges
        }
        response = self._request('POST', '/api/v1/networks', json=data)
        return response.json()
    
    def create_workflow(self, name: str, workflow_type: str, network_id: str, **kwargs) -> Dict[str, Any]:
        """Create a new workflow"""
        data = {
            "name": name,
            "workflow_type": workflow_type,
            "network_id": network_id,
            **kwargs
        }
        response = self._request('POST', '/api/v1/workflows', json=data)
        return response.json()
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        response = self._request('GET', f'/api/v1/workflows/{workflow_id}/status')
        return response.json()

