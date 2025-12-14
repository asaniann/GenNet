"""
Event Sourcing for audit trail and workflow replay
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Type
from enum import Enum
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)

# Try to import SQLAlchemy
try:
    from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Index
    from sqlalchemy.ext.declarative import declarative_base
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None


class EventType(str, Enum):
    """Event type enumeration"""
    # Network events
    NETWORK_CREATED = "network:created"
    NETWORK_UPDATED = "network:updated"
    NETWORK_DELETED = "network:deleted"
    NETWORK_SHARED = "network:shared"
    
    # Workflow events
    WORKFLOW_CREATED = "workflow:created"
    WORKFLOW_STARTED = "workflow:started"
    WORKFLOW_COMPLETED = "workflow:completed"
    WORKFLOW_FAILED = "workflow:failed"
    WORKFLOW_CANCELLED = "workflow:cancelled"
    
    # User events
    USER_CREATED = "user:created"
    USER_UPDATED = "user:updated"
    USER_DELETED = "user:deleted"
    USER_LOGIN = "user:login"
    USER_LOGOUT = "user:logout"
    
    # System events
    API_KEY_CREATED = "api_key:created"
    API_KEY_REVOKED = "api_key:revoked"
    PERMISSION_GRANTED = "permission:granted"
    PERMISSION_REVOKED = "permission:revoked"


@dataclass
class Event:
    """Event data structure"""
    id: str
    event_type: EventType
    aggregate_id: str  # ID of the aggregate (network_id, workflow_id, user_id, etc.)
    aggregate_type: str  # Type of aggregate (network, workflow, user, etc.)
    payload: Dict[str, Any]
    user_id: Optional[int] = None
    correlation_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class EventStore:
    """
    Event store for persisting events
    
    Features:
    - Event persistence
    - Event querying
    - Event replay
    - Audit trail
    """
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self._in_memory_store: List[Event] = []
    
    def append(self, event: Event):
        """Append an event to the store"""
        if self.db_session and SQLALCHEMY_AVAILABLE:
            # Store in database
            event_record = EventRecord(
                id=event.id,
                event_type=event.event_type.value,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                payload=json.dumps(event.payload),
                user_id=event.user_id,
                correlation_id=event.correlation_id,
                timestamp=event.timestamp,
                metadata=json.dumps(event.metadata or {})
            )
            self.db_session.add(event_record)
            self.db_session.commit()
        else:
            # Store in memory
            self._in_memory_store.append(event)
        
        logger.debug(f"Event stored: {event.event_type} for {event.aggregate_type}:{event.aggregate_id}")
    
    def get_events(
        self,
        aggregate_id: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        event_type: Optional[EventType] = None,
        user_id: Optional[int] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """Query events with filters"""
        if self.db_session and SQLALCHEMY_AVAILABLE:
            query = self.db_session.query(EventRecord)
            
            if aggregate_id:
                query = query.filter(EventRecord.aggregate_id == aggregate_id)
            if aggregate_type:
                query = query.filter(EventRecord.aggregate_type == aggregate_type)
            if event_type:
                query = query.filter(EventRecord.event_type == event_type.value)
            if user_id:
                query = query.filter(EventRecord.user_id == user_id)
            if since:
                query = query.filter(EventRecord.timestamp >= since)
            
            query = query.order_by(EventRecord.timestamp.asc())
            
            if limit:
                query = query.limit(limit)
            
            records = query.all()
            return [self._record_to_event(record) for record in records]
        else:
            # Query in-memory store
            events = self._in_memory_store
            
            if aggregate_id:
                events = [e for e in events if e.aggregate_id == aggregate_id]
            if aggregate_type:
                events = [e for e in events if e.aggregate_type == aggregate_type]
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            if user_id:
                events = [e for e in events if e.user_id == user_id]
            if since:
                events = [e for e in events if e.timestamp >= since]
            
            events.sort(key=lambda e: e.timestamp)
            
            if limit:
                events = events[:limit]
            
            return events
    
    def replay_events(
        self,
        aggregate_id: str,
        handler: Callable[[Event], None],
        since: Optional[datetime] = None
    ):
        """
        Replay events for an aggregate
        
        Args:
            aggregate_id: ID of the aggregate
            handler: Function to handle each event
            since: Replay events since this timestamp
        """
        events = self.get_events(aggregate_id=aggregate_id, since=since)
        for event in events:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error replaying event {event.id}: {e}")
                raise
    
    def _record_to_event(self, record) -> Event:
        """Convert database record to Event"""
        return Event(
            id=record.id,
            event_type=EventType(record.event_type),
            aggregate_id=record.aggregate_id,
            aggregate_type=record.aggregate_type,
            payload=json.loads(record.payload),
            user_id=record.user_id,
            correlation_id=record.correlation_id,
            timestamp=record.timestamp,
            metadata=json.loads(record.metadata) if record.metadata else {}
        )


if SQLALCHEMY_AVAILABLE:
    class EventRecord(Base):
        """Database model for events"""
        __tablename__ = "events"
        __table_args__ = (
            Index('idx_event_aggregate', 'aggregate_type', 'aggregate_id'),
            Index('idx_event_type', 'event_type'),
            Index('idx_event_timestamp', 'timestamp'),
            Index('idx_event_user', 'user_id'),
        )
        
        id = Column(String, primary_key=True)
        event_type = Column(String, nullable=False, index=True)
        aggregate_id = Column(String, nullable=False)
        aggregate_type = Column(String, nullable=False)
        payload = Column(JSON, nullable=False)
        user_id = Column(Integer, index=True)
        correlation_id = Column(String)
        timestamp = Column(DateTime, nullable=False, index=True)
        metadata = Column(JSON)
else:
    # Placeholder for when SQLAlchemy not available
    class EventRecord:
        pass


class EventPublisher:
    """
    Publishes events to event store
    
    Usage:
        publisher = EventPublisher(event_store)
        publisher.publish_network_created(network_id, user_id, network_data)
    """
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    def publish(
        self,
        event_type: EventType,
        aggregate_id: str,
        aggregate_type: str,
        payload: Dict[str, Any],
        user_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Publish a generic event"""
        import uuid
        event = Event(
            id=str(uuid.uuid4()),
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            payload=payload,
            user_id=user_id,
            correlation_id=correlation_id,
            metadata=metadata
        )
        self.event_store.append(event)
    
    # Convenience methods for common events
    def publish_network_created(self, network_id: str, user_id: int, network_data: Dict[str, Any]):
        """Publish network created event"""
        self.publish(
            EventType.NETWORK_CREATED,
            network_id,
            "network",
            {"network": network_data},
            user_id=user_id
        )
    
    def publish_workflow_started(self, workflow_id: str, user_id: int, workflow_data: Dict[str, Any]):
        """Publish workflow started event"""
        self.publish(
            EventType.WORKFLOW_STARTED,
            workflow_id,
            "workflow",
            {"workflow": workflow_data},
            user_id=user_id
        )
    
    def publish_user_action(self, event_type: EventType, user_id: int, target_id: str, target_type: str, action_data: Dict[str, Any]):
        """Publish user action event"""
        self.publish(
            event_type,
            target_id,
            target_type,
            action_data,
            user_id=user_id
        )


# Global instances
_event_store: Optional[EventStore] = None
_event_publisher: Optional[EventPublisher] = None


def get_event_store(db_session=None) -> EventStore:
    """Get or create global event store"""
    global _event_store
    if _event_store is None:
        _event_store = EventStore(db_session=db_session)
    return _event_store


def get_event_publisher(db_session=None) -> EventPublisher:
    """Get or create global event publisher"""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher(get_event_store(db_session))
    return _event_publisher


from typing import Callable


