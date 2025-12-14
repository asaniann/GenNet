"""
GraphQL API Service
"""

import logging
import sys
import os
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
import strawberry
from typing import List, Optional

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import correlation ID middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.logging_middleware import CorrelationIDMiddleware, get_logger
from shared.metrics import PrometheusMiddleware, get_metrics_response


@strawberry.type
class NetworkNode:
    id: str
    label: str
    node_type: str


@strawberry.type
class NetworkEdge:
    source: str
    target: str
    edge_type: str
    weight: Optional[float]


@strawberry.type
class Network:
    id: str
    name: str
    description: Optional[str]
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]


@strawberry.type
class Query:
    @strawberry.field
    def networks(self) -> List[Network]:
        """Query networks"""
        # Placeholder - would fetch from database
        return []
    
    @strawberry.field
    def network(self, id: str) -> Optional[Network]:
        """Get a specific network"""
        # Placeholder
        return None


schema = strawberry.Schema(Query)
graphql_app = GraphQLRouter(schema)

app = FastAPI()

# Add correlation ID middleware
# Add middleware (order matters: metrics first, then correlation ID)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(CorrelationIDMiddleware)

app.include_router(graphql_app, prefix="/graphql")

logger = get_logger(__name__)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics_response()


@app.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe"""
    return {
        "status": "ready",
        "service": "graphql-service",
        "version": "1.0.0",
        "checks": {}
    }


@app.get("/health")
async def health():
    """Legacy health endpoint"""
    return await readiness()

