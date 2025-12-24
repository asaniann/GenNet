"""
WebSocket manager for real-time updates
"""

from typing import Dict, Set, Any
import logging
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        """Initialize WebSocket manager"""
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # patient_id -> set of connections
    
    async def connect(self, websocket: WebSocket, patient_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        if patient_id not in self.active_connections:
            self.active_connections[patient_id] = set()
        
        self.active_connections[patient_id].add(websocket)
        logger.info(f"WebSocket connected for patient: {patient_id}")
    
    def disconnect(self, websocket: WebSocket, patient_id: str):
        """Remove WebSocket connection"""
        if patient_id in self.active_connections:
            self.active_connections[patient_id].discard(websocket)
            if not self.active_connections[patient_id]:
                del self.active_connections[patient_id]
        logger.info(f"WebSocket disconnected for patient: {patient_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast_to_patient(self, patient_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for a patient"""
        if patient_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[patient_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to patient {patient_id}: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.active_connections[patient_id].discard(conn)
    
    async def send_heartbeat(self, websocket: WebSocket):
        """Send heartbeat to keep connection alive"""
        try:
            await websocket.send_json({"type": "heartbeat", "timestamp": asyncio.get_event_loop().time()})
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")

