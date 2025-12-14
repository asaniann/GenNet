"""
WebSocket manager for real-time updates
"""
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    WORKFLOW_UPDATE = "workflow_update"
    NETWORK_UPDATE = "network_update"
    COLLABORATION_UPDATE = "collaboration_update"
    NOTIFICATION = "notification"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates
    
    Supports:
    - Multiple rooms/channels (e.g., workflow_id, network_id)
    - Broadcast to all or specific rooms
    - Connection management
    - Heartbeat/ping-pong
    """
    
    def __init__(self):
        # Map of room_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket -> set of room_ids
        self.connection_rooms: Dict[WebSocket, Set[str]] = {}
        # Heartbeat interval (seconds)
        self.heartbeat_interval = 30
    
    async def connect(self, websocket: WebSocket, room_id: str):
        """
        Connect a WebSocket to a room
        
        Args:
            websocket: WebSocket connection
            room_id: Room/channel identifier (e.g., workflow_id, network_id)
        """
        await websocket.accept()
        
        # Add to room
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
        
        # Track rooms for this connection
        if websocket not in self.connection_rooms:
            self.connection_rooms[websocket] = set()
        self.connection_rooms[websocket].add(room_id)
        
        logger.info(f"WebSocket connected to room {room_id} (total: {len(self.active_connections.get(room_id, set()))})")
        
        # Start heartbeat
        asyncio.create_task(self._heartbeat(websocket))
    
    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket from all rooms
        
        Args:
            websocket: WebSocket connection to disconnect
        """
        # Remove from all rooms
        if websocket in self.connection_rooms:
            for room_id in self.connection_rooms[websocket]:
                if room_id in self.active_connections:
                    self.active_connections[room_id].discard(websocket)
                    if not self.active_connections[room_id]:
                        del self.active_connections[room_id]
            
            del self.connection_rooms[websocket]
        
        logger.info(f"WebSocket disconnected")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection
        
        Args:
            message: Message dictionary
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_room(self, message: dict, room_id: str, exclude: Optional[WebSocket] = None):
        """
        Broadcast a message to all connections in a room
        
        Args:
            message: Message dictionary
            room_id: Room identifier
            exclude: WebSocket connection to exclude from broadcast
        """
        if room_id not in self.active_connections:
            return
        
        disconnected = set()
        for websocket in self.active_connections[room_id]:
            if websocket == exclude:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to room {room_id}: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_to_all(self, message: dict, exclude: Optional[WebSocket] = None):
        """
        Broadcast a message to all connected WebSockets
        
        Args:
            message: Message dictionary
            exclude: WebSocket connection to exclude
        """
        all_connections = set()
        for room_connections in self.active_connections.values():
            all_connections.update(room_connections)
        
        disconnected = set()
        for websocket in all_connections:
            if websocket == exclude:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def _heartbeat(self, websocket: WebSocket):
        """Send periodic heartbeat (ping) to keep connection alive"""
        try:
            while websocket in self.connection_rooms:
                await asyncio.sleep(self.heartbeat_interval)
                try:
                    await websocket.send_json({
                        "type": MessageType.PING.value,
                        "timestamp": asyncio.get_event_loop().time()
                    })
                except Exception:
                    break
        except asyncio.CancelledError:
            pass
        finally:
            self.disconnect(websocket)
    
    def get_room_connections_count(self, room_id: str) -> int:
        """Get number of connections in a room"""
        return len(self.active_connections.get(room_id, set()))
    
    def get_total_connections_count(self) -> int:
        """Get total number of active connections"""
        return len(self.connection_rooms)


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get or create global WebSocket manager instance"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


def create_workflow_update_message(workflow_id: str, status: str, progress: int, data: Optional[dict] = None) -> dict:
    """Create a workflow update message"""
    return {
        "type": MessageType.WORKFLOW_UPDATE.value,
        "workflow_id": workflow_id,
        "status": status,
        "progress": progress,
        "data": data or {},
        "timestamp": asyncio.get_event_loop().time()
    }


def create_network_update_message(network_id: str, action: str, data: Optional[dict] = None) -> dict:
    """Create a network update message"""
    return {
        "type": MessageType.NETWORK_UPDATE.value,
        "network_id": network_id,
        "action": action,  # created, updated, deleted
        "data": data or {},
        "timestamp": asyncio.get_event_loop().time()
    }


def create_notification_message(title: str, message: str, level: str = "info", data: Optional[dict] = None) -> dict:
    """Create a notification message"""
    return {
        "type": MessageType.NOTIFICATION.value,
        "title": title,
        "message": message,
        "level": level,  # info, warning, error, success
        "data": data or {},
        "timestamp": asyncio.get_event_loop().time()
    }

