"""
Audit logging for compliance and security
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import os

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logging for compliance"""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize audit logger"""
        self.db = db
    
    def log_access(
        self,
        user_id: int,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log access to resource
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action performed
            success: Whether action was successful
            metadata: Additional metadata
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "success": success,
            "metadata": metadata or {}
        }
        
        # Log to application logs
        logger.info(f"Audit: {log_entry}")
        
        # Publish to Kafka for centralized audit log
        try:
            from shared.kafka_publisher import KafkaEventPublisher
            KafkaEventPublisher.publish_event(
                topic="audit-logs",
                event={
                    "event_type": "access_log",
                    **log_entry
                },
                key=str(user_id)
            )
        except Exception as e:
            logger.warning(f"Could not publish audit log to Kafka: {e}")
    
    def log_data_modification(
        self,
        user_id: int,
        resource_type: str,
        resource_id: str,
        changes: Dict[str, Any],
        patient_id: Optional[str] = None
    ):
        """
        Log data modification
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: Resource ID
            changes: Dictionary of changes
            patient_id: Optional patient ID (for PHI)
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": "modify",
            "changes": changes,
            "patient_id": patient_id
        }
        
        logger.info(f"Audit: Data modification: {log_entry}")
        
        # Publish to Kafka
        try:
            from shared.kafka_publisher import KafkaEventPublisher
            KafkaEventPublisher.publish_event(
                topic="audit-logs",
                event={
                    "event_type": "data_modification",
                    **log_entry
                },
                key=patient_id or resource_id
            )
        except Exception as e:
            logger.warning(f"Could not publish audit log to Kafka: {e}")
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[int],
        details: Dict[str, Any]
    ):
        """
        Log security event
        
        Args:
            event_type: Type of security event
            user_id: User ID (if applicable)
            details: Event details
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        }
        
        logger.warning(f"Security Event: {log_entry}")
        
        # Publish to Kafka for security monitoring
        try:
            from shared.kafka_publisher import KafkaEventPublisher
            KafkaEventPublisher.publish_event(
                topic="security-events",
                event={
                    "event_type": event_type,
                    **log_entry
                },
                key=str(user_id) if user_id else "anonymous"
            )
        except Exception as e:
            logger.warning(f"Could not publish security event to Kafka: {e}")

