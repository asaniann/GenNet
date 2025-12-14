"""
Batch operations for GRN networks
"""
from typing import List, Dict, Any
from models import GRNNetwork, GRNNetworkCreate
from database import SessionLocal
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


async def create_networks_batch(
    networks: List[Dict[str, Any]],
    user_id: int,
    neo4j_client=None
) -> List[Dict[str, Any]]:
    """
    Create multiple networks in a single transaction
    
    Args:
        networks: List of network data dictionaries
        user_id: User ID creating the networks
        neo4j_client: Optional Neo4j client
    
    Returns:
        List of created network IDs and status
    """
    db = SessionLocal()
    results = []
    
    try:
        for network_data in networks:
            try:
                network_id = str(uuid.uuid4())
                
                # Create database record
                db_network = GRNNetwork(
                    id=network_id,
                    name=network_data.get('name', 'Unnamed Network'),
                    description=network_data.get('description'),
                    owner_id=user_id,
                    created_at=datetime.utcnow()
                )
                db.add(db_network)
                
                # Store in Neo4j if available
                if neo4j_client and 'nodes' in network_data:
                    try:
                        neo4j_client.create_network(
                            network_id,
                            network_data.get('nodes', []),
                            network_data.get('edges', [])
                        )
                    except Exception as e:
                        logger.warning(f"Failed to store network {network_id} in Neo4j: {e}")
                
                results.append({
                    "id": network_id,
                    "name": db_network.name,
                    "status": "created"
                })
                
            except Exception as e:
                logger.error(f"Failed to create network: {e}")
                results.append({
                    "error": str(e),
                    "status": "failed"
                })
        
        # Commit all networks
        db.commit()
        
        # Refresh all networks
        for result in results:
            if result.get("status") == "created":
                db.refresh(db.query(GRNNetwork).filter(GRNNetwork.id == result["id"]).first())
        
        return results
        
    except Exception as e:
        db.rollback()
        logger.error(f"Batch creation failed: {e}")
        raise
    finally:
        db.close()


async def delete_networks_batch(
    network_ids: List[str],
    user_id: int,
    neo4j_client=None
) -> Dict[str, Any]:
    """
    Delete multiple networks in a single transaction
    
    Args:
        network_ids: List of network IDs to delete
        user_id: User ID (for authorization)
        neo4j_client: Optional Neo4j client
    
    Returns:
        Dictionary with deletion results
    """
    db = SessionLocal()
    deleted = []
    failed = []
    
    try:
        for network_id in network_ids:
            try:
                network = db.query(GRNNetwork).filter(
                    GRNNetwork.id == network_id,
                    GRNNetwork.owner_id == user_id
                ).first()
                
                if network:
                    # Delete from Neo4j
                    if neo4j_client:
                        try:
                            neo4j_client.delete_network(network_id)
                        except Exception as e:
                            logger.warning(f"Failed to delete network {network_id} from Neo4j: {e}")
                    
                    db.delete(network)
                    deleted.append(network_id)
                else:
                    failed.append({"id": network_id, "error": "not found or unauthorized"})
                    
            except Exception as e:
                logger.error(f"Failed to delete network {network_id}: {e}")
                failed.append({"id": network_id, "error": str(e)})
        
        db.commit()
        
        return {
            "deleted": deleted,
            "failed": failed,
            "total_requested": len(network_ids),
            "total_deleted": len(deleted),
            "total_failed": len(failed)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Batch deletion failed: {e}")
        raise
    finally:
        db.close()


