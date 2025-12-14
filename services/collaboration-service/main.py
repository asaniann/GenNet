"""
Collaboration Service
Real-time collaboration, presence, and version control
"""

import logging
import sys
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Dict, List, Set
import json
import redis

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

app = FastAPI(
    title="GenNet Collaboration Service",
    description="Real-time Collaboration and Version Control",
    version="1.0.0"
)

# Add correlation ID middleware
# Add middleware (order matters: metrics first, then correlation ID)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(CorrelationIDMiddleware)

logger = get_logger(__name__)

redis_client = redis.Redis(host='redis', port=6379, db=1, decode_responses=True)

# Store active connections per resource
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections"""
    
    async def connect(self, websocket: WebSocket, resource_id: str):
        await websocket.accept()
        if resource_id not in active_connections:
            active_connections[resource_id] = set()
        active_connections[resource_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, resource_id: str):
        if resource_id in active_connections:
            active_connections[resource_id].discard(websocket)
    
    async def broadcast(self, resource_id: str, message: dict, sender: WebSocket = None):
        if resource_id in active_connections:
            for connection in active_connections[resource_id]:
                if connection != sender:
                    await connection.send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/{resource_type}/{resource_id}")
async def websocket_endpoint(websocket: WebSocket, resource_type: str, resource_id: str):
    """WebSocket endpoint for real-time collaboration"""
    resource_key = f"{resource_type}:{resource_id}"
    await manager.connect(websocket, resource_key)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Broadcast to other users
            await manager.broadcast(resource_key, message, sender=websocket)
            
            # Store in Redis for persistence
            redis_client.lpush(f"messages:{resource_key}", json.dumps(message))
            redis_client.ltrim(f"messages:{resource_key}", 0, 999)  # Keep last 1000 messages
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, resource_key)


@app.get("/presence/{resource_type}/{resource_id}")
async def get_presence(resource_type: str, resource_id: str):
    """Get active users for a resource"""
    resource_key = f"{resource_type}:{resource_id}"
    count = len(active_connections.get(resource_key, set()))
    return {"active_users": count}


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
    import redis
    checks = {}
    all_ready = True
    
    # Check Redis connection (critical for collaboration)
    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        all_ready = False
    
    status = "ready" if all_ready else "not_ready"
    status_code = 200 if all_ready else 503
    
    return JSONResponse(
        content={
            "status": status,
            "service": "collaboration-service",
            "version": "1.0.0",
            "checks": checks
        },
        status_code=status_code
    )


@app.get("/health")
async def health():
    """Legacy health endpoint"""
    return await readiness()

