"""
Kafka client for real-time event streaming
"""

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from typing import Dict, Any, Optional, Callable
import json
import logging
import os

logger = logging.getLogger(__name__)


class KafkaClient:
    """Kafka producer and consumer client"""
    
    def __init__(self):
        """Initialize Kafka client"""
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.producer = None
        self.consumers = {}
    
    def get_producer(self) -> KafkaProducer:
        """Get or create Kafka producer"""
        if self.producer is None:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3
            )
        return self.producer
    
    def publish_event(
        self,
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
            True if successful
        """
        try:
            producer = self.get_producer()
            future = producer.send(topic, value=event, key=key)
            future.get(timeout=10)  # Wait for confirmation
            logger.info(f"Published event to topic {topic}: {event.get('event_type')}")
            return True
        except KafkaError as e:
            logger.error(f"Error publishing event to Kafka: {e}")
            return False
    
    def create_consumer(
        self,
        topic: str,
        group_id: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> KafkaConsumer:
        """
        Create Kafka consumer for a topic
        
        Args:
            topic: Kafka topic name
            group_id: Consumer group ID
            callback: Function to call for each message
            
        Returns:
            KafkaConsumer instance
        """
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        
        self.consumers[topic] = consumer
        
        # Start consuming in background thread
        import threading
        thread = threading.Thread(
            target=self._consume_messages,
            args=(consumer, callback),
            daemon=True
        )
        thread.start()
        
        return consumer
    
    def _consume_messages(
        self,
        consumer: KafkaConsumer,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """Consume messages from Kafka"""
        try:
            for message in consumer:
                try:
                    callback(message.value)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except Exception as e:
            logger.error(f"Error consuming from Kafka: {e}")
    
    def close(self):
        """Close all connections"""
        if self.producer:
            self.producer.close()
        for consumer in self.consumers.values():
            consumer.close()

