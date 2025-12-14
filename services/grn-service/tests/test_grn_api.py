"""
API tests for GRN service
"""

import pytest
from fastapi import status


@pytest.mark.integration
def test_create_network(client, auth_headers, mock_neo4j):
    """Test creating a network"""
    network_data = {
        "name": "Test Network",
        "description": "A test network",
        "nodes": [
            {"id": "gene1", "label": "Gene 1", "node_type": "gene"},
            {"id": "gene2", "label": "Gene 2", "node_type": "gene"}
        ],
        "edges": [
            {"source": "gene1", "target": "gene2", "edge_type": "activates"}
        ]
    }
    
    response = client.post(
        "/networks",
        json=network_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["name"] == network_data["name"]
    assert mock_neo4j.create_network.called


@pytest.mark.integration
def test_list_networks(client, test_network, auth_headers):
    """Test listing networks"""
    response = client.get("/networks", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.integration
def test_get_network(client, test_network, auth_headers, mock_neo4j):
    """Test getting a network"""
    mock_neo4j.get_network.return_value = {
        "nodes": [{"id": "gene1", "label": "Gene 1"}],
        "edges": []
    }
    
    response = client.get(
        f"/networks/{test_network.id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_network.id
    assert "nodes" in data


@pytest.mark.integration
def test_get_network_not_found(client, auth_headers):
    """Test getting non-existent network"""
    response = client.get(
        "/networks/nonexistent",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
def test_update_network(client, test_network, auth_headers, mock_neo4j):
    """Test updating a network"""
    update_data = {
        "name": "Updated Network",
        "description": "Updated description",
        "nodes": [],
        "edges": []
    }
    
    response = client.put(
        f"/networks/{test_network.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_data["name"]


@pytest.mark.integration
def test_delete_network(client, test_network, auth_headers, mock_neo4j):
    """Test deleting a network"""
    response = client.delete(
        f"/networks/{test_network.id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert mock_neo4j.delete_network.called


@pytest.mark.integration
def test_validate_network(client, test_network, auth_headers):
    """Test network validation"""
    response = client.post(
        f"/networks/{test_network.id}/validate",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "is_valid" in data


@pytest.mark.integration
def test_health_check(client):
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

