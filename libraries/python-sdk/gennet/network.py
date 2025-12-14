"""Network model"""

from typing import List, Dict, Any


class Network:
    """Represents a GRN network"""
    
    def __init__(self, data: Dict[str, Any], client=None):
        self.id = data['id']
        self.name = data['name']
        self.description = data.get('description')
        self.nodes = data.get('nodes', [])
        self.edges = data.get('edges', [])
        self._client = client
    
    def __repr__(self):
        return f"<Network id={self.id} name={self.name}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'nodes': self.nodes,
            'edges': self.edges
        }

