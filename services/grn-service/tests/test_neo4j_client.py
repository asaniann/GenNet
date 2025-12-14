"""
Tests for Neo4j client
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.unit
@patch('neo4j_client.GraphDatabase')
@patch.dict('os.environ', {'NEO4J_URI': 'bolt://localhost:7687', 'NEO4J_USER': 'test', 'NEO4J_PASSWORD': 'test'})
def test_neo4j_client_initialization(mock_graph_db):
    """Test Neo4j client initialization"""
    from neo4j_client import Neo4jClient
    mock_driver = Mock()
    mock_graph_db.driver.return_value = mock_driver
    
    client = Neo4jClient()
    assert client.driver == mock_driver


@pytest.mark.unit
def test_create_network():
    """Test network creation in Neo4j"""
    from neo4j_client import Neo4jClient
    
    mock_session = Mock()
    mock_session.run.return_value = []
    
    mock_driver = Mock()
    mock_context = Mock()
    mock_context.__enter__.return_value = mock_session
    mock_context.__exit__.return_value = None
    mock_driver.session.return_value = mock_context
    
    client = Neo4jClient()
    client.driver = mock_driver
    
    nodes = [
        {"id": "gene1", "label": "Gene 1", "node_type": "gene"}
    ]
    edges = [
        {"source": "gene1", "target": "gene2", "edge_type": "activates", "weight": 1.0}
    ]
    
    client.create_network("network-1", nodes, edges)
    
    assert mock_session.run.called


@pytest.mark.unit
def test_get_network():
    """Test network retrieval from Neo4j"""
    from neo4j_client import Neo4jClient
    
    mock_record = Mock()
    mock_record.__getitem__.side_effect = lambda key: {
        "g": {"id": "gene1", "label": "Gene 1", "type": "gene"},
        "edges": []
    }[key]
    
    mock_session = Mock()
    mock_session.run.return_value = [mock_record]
    
    mock_driver = Mock()
    mock_context = Mock()
    mock_context.__enter__.return_value = mock_session
    mock_context.__exit__.return_value = None
    mock_driver.session.return_value = mock_context
    
    client = Neo4jClient()
    client.driver = mock_driver
    
    result = client.get_network("network-1")
    
    assert "nodes" in result
    assert "edges" in result

