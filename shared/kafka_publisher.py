"""
Shared Kafka event publisher
Used by services to publish events to Kafka
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaEventPublisher:
    """Shared Kafka event publisher for services"""
    
    _producer: Optional[KafkaProducer] = None
    
    @classmethod
    def get_producer(cls) -> Optional[KafkaProducer]:
        """Get or create Kafka producer"""
        if cls._producer is None:
            bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
            if not bootstrap_servers:
                logger.warning("KAFKA_BOOTSTRAP_SERVERS not set, Kafka publishing disabled")
                return None
            
            try:
                cls._producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',
                    retries=3
                )
            except Exception as e:
                logger.error(f"Error creating Kafka producer: {e}")
                return None
        
        return cls._producer
    
    @classmethod
    def publish_event(
        cls,
        topic: str,
        event: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """
        Publish event to Kafka topic
        
        Args:
            topic: Kafka topic name
            event: Event data dictionary
            key: Optional partition key
            
        Returns:
            True if successful, False otherwise
        """
        producer = cls.get_producer()
        if not producer:
            return False
        
        try:
            future = producer.send(topic, value=event, key=key)
            future.get(timeout=10)
            logger.debug(f"Published event to topic {topic}: {event.get('event_type')}")
            return True
        except KafkaError as e:
            logger.error(f"Error publishing event to Kafka: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing event: {e}")
            return False

