"""
GRN Service - Gene Regulatory Network Management
Handles network creation, storage, querying, and manipulation
"""

import logging
import sys
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime
import os

from models import GRNNetwork, GRNNetworkCreate, GRNNetworkResponse, Node, Edge
from database import get_db, init_db
from neo4j_client import Neo4jClient
from s3_client import S3Client
from dependencies import get_current_user_id

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import shared middleware and utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.logging_middleware import CorrelationIDMiddleware, get_logger
from shared.metrics import PrometheusMiddleware, get_metrics_response
from shared.cache import cached, invalidate_cache
from shared.validation import NetworkCreateValidator, PaginationParams
from shared.pagination import CursorPaginationParams, paginate_with_cursor, PaginatedResponse
from shared.error_handler import setup_error_handlers
from shared.exceptions import NotFoundError, ValidationError
from shared.compression import setup_compression
from shared.api_versioning import APIVersion, get_api_version, require_version

app = FastAPI(
    title="GenNet GRN Service",
    description="Gene Regulatory Network Management Service",
    version="1.0.0"
)

# Setup error handlers
setup_error_handlers(app)

# Setup compression
setup_compression(app, minimum_size=512, prefer_brotli=True)

# Add middleware (order matters: metrics first, then correlation ID, then compression)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(CorrelationIDMiddleware)

logger = get_logger(__name__)

# Initialize clients with error handling
try:
    neo4j_client = Neo4jClient()
except Exception:
    neo4j_client = None  # Will be mocked in tests

try:
    s3_client = S3Client()
except Exception:
    s3_client = None  # Will be mocked in tests


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting GRN Service...")
    init_db()
    logger.info("GRN Service started successfully")


@app.post("/networks/batch", status_code=status.HTTP_201_CREATED)
async def create_networks_batch(
    networks: List[Dict[str, Any]],
    user_id: int = Depends(get_current_user_id)
):
    """Create multiple networks in a single request (batch operation)"""
    from batch_operations import create_networks_batch
    results = await create_networks_batch(networks, user_id, neo4j_client)
    return {"results": results, "total": len(networks)}


@app.delete("/networks/batch", status_code=status.HTTP_200_OK)
async def delete_networks_batch(
    network_ids: List[str],
    user_id: int = Depends(get_current_user_id)
):
    """Delete multiple networks in a single request (batch operation)"""
    from batch_operations import delete_networks_batch
    result = await delete_networks_batch(network_ids, user_id, neo4j_client)
    return result


@app.post("/networks", response_model=GRNNetworkResponse, status_code=status.HTTP_201_CREATED)
async def create_network(
    network: GRNNetworkCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new GRN network with enhanced validation"""
    logger.info(f"Creating network: {network.name} (user_id: {user_id}, nodes: {len(network.nodes)}, edges: {len(network.edges)})")
    db_network = GRNNetwork(
        id=str(uuid.uuid4()),
        name=network.name,
        description=network.description,
        owner_id=user_id,
        created_at=datetime.utcnow()
    )
    db.add(db_network)
    db.commit()
    db.refresh(db_network)
    
    # Store network graph in Neo4j
    if neo4j_client:
        try:
            neo4j_client.create_network(db_network.id, network.nodes, network.edges)
        except Exception as e:
            # Log error but continue (for development)
            print(f"Neo4j error: {e}")
    
    return db_network


@app.get(
    "/networks",
    response_model=Union[PaginatedResponse[GRNNetworkResponse], List[GRNNetworkResponse]],
    summary="List networks",
    description="List all GRN networks accessible to the current user. Supports both cursor-based and offset-based pagination.",
    tags=["Networks"],
    responses={
        200: {
            "description": "List of networks",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {"id": "net-123", "name": "My Network", "owner_id": 1}
                        ],
                        "next_cursor": "eyJ2YWx1ZSI6IjIwMjQtMDEtMDE...",
                        "limit": 50,
                        "has_more": True
                    }
                }
            }
        }
    }
)
async def list_networks(
    cursor: Optional[str] = None,
    limit: int = 50,
    skip: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all networks accessible to the user with cursor-based pagination
    
    Use cursor parameter for efficient pagination of large datasets.
    If skip is provided, falls back to offset-based pagination (legacy).
    """
    query = db.query(GRNNetwork).filter(GRNNetwork.owner_id == user_id)
    
    # Use cursor-based pagination if cursor is provided, else use offset
    if cursor is not None or skip is None:
        # Cursor-based pagination
        result = paginate_with_cursor(
            query=query,
            limit=min(limit, 100),
            cursor=cursor,
            sort_field="created_at",
            sort_desc=True,
            entity_class=GRNNetwork
        )
        return result
    else:
        # Legacy offset-based pagination
        networks = query.order_by(GRNNetwork.created_at.desc()).offset(skip).limit(min(limit, 100)).all()
        return networks


@app.get("/networks/{network_id}", response_model=GRNNetworkResponse)
async def get_network(
    network_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get a specific network"""
    network = db.query(GRNNetwork).filter(
        GRNNetwork.id == network_id,
        GRNNetwork.owner_id == user_id
    ).first()
    if not network:
        raise NotFoundError("Network", network_id)
    
    # Fetch graph data from Neo4j
    graph_data = neo4j_client.get_network(network_id)
    network.nodes = graph_data.get("nodes", [])
    network.edges = graph_data.get("edges", [])
    
    return network


@app.put("/networks/{network_id}", response_model=GRNNetworkResponse)
async def update_network(
    network_id: str,
    network_update: GRNNetworkCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update a network"""
    network = db.query(GRNNetwork).filter(
        GRNNetwork.id == network_id,
        GRNNetwork.owner_id == user_id
    ).first()
    if not network:
        raise NotFoundError("Network", network_id)
    
    network.name = network_update.name
    network.description = network_update.description
    network.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(network)
    
    # Update graph in Neo4j
    neo4j_client.update_network(network_id, network_update.nodes, network_update.edges)
    
    return network


@app.delete("/networks/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_network(
    network_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete a network"""
    network = db.query(GRNNetwork).filter(
        GRNNetwork.id == network_id,
        GRNNetwork.owner_id == user_id
    ).first()
    if not network:
        raise NotFoundError("Network", network_id)
    
    # Delete from Neo4j
    neo4j_client.delete_network(network_id)
    
    # Delete from database
    db.delete(network)
    db.commit()


@app.post("/networks/{network_id}/validate")
async def validate_network(
    network_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Validate network structure and CTL formulas"""
    network = db.query(GRNNetwork).filter(
        GRNNetwork.id == network_id,
        GRNNetwork.owner_id == user_id
    ).first()
    if not network:
        raise NotFoundError("Network", network_id)
    
    # Fetch graph from Neo4j
    graph_data = neo4j_client.get_network(network_id)
    
    # Perform validation (basic checks)
    validation_results = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check for cycles, disconnected components, etc.
    # This is a placeholder - implement actual validation logic
    
    return validation_results


@app.get("/networks/{network_id}/subgraph")
async def get_subgraph(
    network_id: str,
    node_ids: List[str],
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Extract a subgraph from the network"""
    network = db.query(GRNNetwork).filter(
        GRNNetwork.id == network_id,
        GRNNetwork.owner_id == user_id
    ).first()
    if not network:
        raise NotFoundError("Network", network_id)
    
    subgraph = neo4j_client.get_subgraph(network_id, node_ids)
    return subgraph


@app.post("/networks/import")
async def import_network(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Import a network from file (SBML, BioPAX, JSON, etc.)"""
    content = await file.read()
    
    # Parse file based on extension
    # This is a placeholder - implement actual import logic
    
    return {"message": "Import functionality to be implemented"}


@app.get("/networks/{network_id}/export")
async def export_network(
    network_id: str,
    format: str = "json",
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Export a network to file"""
    network = db.query(GRNNetwork).filter(
        GRNNetwork.id == network_id,
        GRNNetwork.owner_id == user_id
    ).first()
    if not network:
        raise NotFoundError("Network", network_id)
    
    graph_data = neo4j_client.get_network(network_id)
    
    # Export based on format
    # This is a placeholder - implement actual export logic
    
    return {"message": "Export functionality to be implemented"}


@app.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe"""
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "grn-service",
        "version": "1.0.0"
    }
    checks = {}
    all_ready = True
    
    # Check database connection (critical)
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        all_ready = False
    
    # Check Neo4j connection (critical for graph operations)
    try:
        if neo4j_client and neo4j_client.driver:
            with neo4j_client.driver.session() as session:
                session.run("RETURN 1")
            checks["neo4j"] = "ok"
        else:
            checks["neo4j"] = "not_configured"
            # Neo4j is critical, but allow service to start
    except Exception as e:
        checks["neo4j"] = f"error: {str(e)}"
        # Don't fail readiness if Neo4j is unavailable in dev
    
    health_status["checks"] = checks
    health_status["status"] = "ready" if all_ready else "not_ready"
    
    status_code = 200 if all_ready else 503
    return JSONResponse(
        content=health_status,
        status_code=status_code
    )


@app.get("/health")
async def health():
    """Legacy health endpoint"""
    return await readiness()

