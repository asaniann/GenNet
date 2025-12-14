"""
Neo4j client for graph database operations
"""

from neo4j import GraphDatabase
import os
from typing import List, Dict, Any, Optional


class Neo4jClient:
    """Client for interacting with Neo4j graph database"""
    
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "gennet_dev")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        """Close the driver connection"""
        self.driver.close()
    
    def create_network(self, network_id: str, nodes: List[Dict], edges: List[Dict]):
        """Create a network graph in Neo4j"""
        with self.driver.session() as session:
            # Create network node
            session.run(
                "CREATE (n:Network {id: $network_id})",
                network_id=network_id
            )
            
            # Create gene/protein nodes
            for node in nodes:
                session.run(
                    """
                    MATCH (net:Network {id: $network_id})
                    CREATE (g:Gene {
                        id: $node_id,
                        label: $label,
                        type: $node_type
                    })
                    CREATE (net)-[:CONTAINS]->(g)
                    """,
                    network_id=network_id,
                    node_id=node.id,
                    label=node.label,
                    node_type=node.node_type
                )
            
            # Create edges
            for edge in edges:
                session.run(
                    """
                    MATCH (source:Gene {id: $source})
                    MATCH (target:Gene {id: $target})
                    CREATE (source)-[r:REGULATES {
                        type: $edge_type,
                        weight: $weight
                    }]->(target)
                    """,
                    source=edge.source,
                    target=edge.target,
                    edge_type=edge.edge_type,
                    weight=edge.weight
                )
    
    def get_network(self, network_id: str) -> Dict[str, Any]:
        """Retrieve network graph from Neo4j"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (net:Network {id: $network_id})-[:CONTAINS]->(g:Gene)
                OPTIONAL MATCH (g)-[r:REGULATES]->(target:Gene)
                WHERE (target)<-[:CONTAINS]-(net)
                RETURN g, collect(DISTINCT {target: target.id, type: r.type, weight: r.weight}) as edges
                """,
                network_id=network_id
            )
            
            nodes = []
            edges = []
            for record in result:
                node_data = dict(record["g"])
                nodes.append({
                    "id": node_data["id"],
                    "label": node_data["label"],
                    "type": node_data.get("type", "gene")
                })
                for edge_data in record["edges"]:
                    if edge_data["target"]:
                        edges.append({
                            "source": node_data["id"],
                            "target": edge_data["target"],
                            "type": edge_data["type"],
                            "weight": edge_data["weight"]
                        })
            
            return {"nodes": nodes, "edges": edges}
    
    def update_network(self, network_id: str, nodes: List[Dict], edges: List[Dict]):
        """Update network graph in Neo4j"""
        # Delete existing network
        self.delete_network(network_id)
        # Recreate with new data
        self.create_network(network_id, nodes, edges)
    
    def delete_network(self, network_id: str):
        """Delete network from Neo4j"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (net:Network {id: $network_id})
                OPTIONAL MATCH (net)-[:CONTAINS]->(g:Gene)
                DETACH DELETE net, g
                """,
                network_id=network_id
            )
    
    def get_subgraph(self, network_id: str, node_ids: List[str]) -> Dict[str, Any]:
        """Extract subgraph for specified nodes"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (net:Network {id: $network_id})-[:CONTAINS]->(g:Gene)
                WHERE g.id IN $node_ids
                OPTIONAL MATCH (g)-[r:REGULATES]->(target:Gene)
                WHERE target.id IN $node_ids AND (target)<-[:CONTAINS]-(net)
                RETURN g, collect(DISTINCT {target: target.id, type: r.type, weight: r.weight}) as edges
                """,
                network_id=network_id,
                node_ids=node_ids
            )
            
            nodes = []
            edges = []
            for record in result:
                node_data = dict(record["g"])
                nodes.append({
                    "id": node_data["id"],
                    "label": node_data["label"],
                    "type": node_data.get("type", "gene")
                })
                for edge_data in record["edges"]:
                    if edge_data["target"]:
                        edges.append({
                            "source": node_data["id"],
                            "target": edge_data["target"],
                            "type": edge_data["type"],
                            "weight": edge_data["weight"]
                        })
            
            return {"nodes": nodes, "edges": edges}

