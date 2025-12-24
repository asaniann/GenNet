"""
Real-Time Processing Service
Kafka integration and WebSocket support for real-time updates
"""

import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio

from models import RealTimeEvent, Alert, EventRequest, EventResponse, AlertResponse
from database import get_db, init_db
from dependencies import get_current_user_id
from kafka_client import KafkaClient
from stream_processor import StreamProcessor
from realtime_predictor import RealTimePredictor
from alert_engine import AlertEngine
from websocket_manager import WebSocketManager

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import shared middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.logging_middleware import CorrelationIDMiddleware, get_logger
from shared.metrics import PrometheusMiddleware, get_metrics_response
from shared.error_handler import setup_error_handlers
from shared.exceptions import NotFoundError, ValidationError
from shared.compression import setup_compression

app = FastAPI(
    title="GenNet Real-Time Processing Service",
    description="Real-Time Event Processing and Streaming Service",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup error handlers
setup_error_handlers(app)
setup_compression(app, minimum_size=512, prefer_brotli=True)

# Add middleware
app.add_middleware(PrometheusMiddleware)
app.add_middleware(CorrelationIDMiddleware)

logger = get_logger(__name__)

# Initialize components
kafka_client = KafkaClient()
stream_processor = StreamProcessor()
realtime_predictor = RealTimePredictor()
alert_engine = AlertEngine()
websocket_manager = WebSocketManager()


@app.on_event("startup")
async def startup_event():
    """Initialize database and start Kafka consumers"""
    logger.info("Starting Real-Time Processing Service...")
    init_db()
    
    # Start Kafka consumers for different topics
    kafka_client.create_consumer(
        topic="patient-events",
        group_id="realtime-processor",
        callback=handle_patient_event
    )
    
    logger.info("Real-Time Processing Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Close Kafka connections"""
    kafka_client.close()


def handle_patient_event(event: Dict[str, Any]):
    """Handle incoming Kafka event"""
    # Process event
    processed = stream_processor.process_event(event)
    
    # Generate prediction if needed
    # prediction = await realtime_predictor.predict_from_event(processed)
    
    # Check for alerts
    alerts = alert_engine.check_event_for_alerts(processed)
    
    # Broadcast to WebSocket connections
    patient_id = event.get("patient_id")
    if patient_id:
        # Would broadcast asynchronously
        pass


@app.post("/stream/publish", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def publish_event(
    request: EventRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Publish event to Kafka stream"""
    logger.info(f"Publishing event: {request.event_type} for patient: {request.patient_id}")
    
    # Store event in database
    event = RealTimeEvent(
        id=str(uuid.uuid4()),
        patient_id=request.patient_id,
        event_type=request.event_type,
        event_data=request.event_data,
        timestamp=datetime.utcnow()
    )
    db.add(event)
    db.commit()
    
    # Publish to Kafka
    kafka_event = {
        "id": event.id,
        "patient_id": request.patient_id,
        "event_type": request.event_type,
        "event_data": request.event_data,
        "timestamp": event.timestamp.isoformat()
    }
    
    kafka_client.publish_event(
        topic="patient-events",
        event=kafka_event,
        key=request.patient_id
    )
    
    return EventResponse(
        id=event.id,
        patient_id=event.patient_id,
        event_type=event.event_type,
        timestamp=event.timestamp
    )


@app.get("/alerts/{patient_id}", response_model=List[AlertResponse])
async def get_patient_alerts(
    patient_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get alerts for a patient"""
    alerts = db.query(Alert).filter(
        Alert.patient_id == patient_id,
        Alert.acknowledged == False
    ).order_by(Alert.created_at.desc()).limit(50).all()
    
    return [
        AlertResponse(
            id=alert.id,
            patient_id=alert.patient_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            created_at=alert.created_at
        )
        for alert in alerts
    ]


@app.websocket("/ws/{patient_id}")
async def websocket_endpoint(websocket: WebSocket, patient_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket, patient_id)
    try:
        while True:
            # Send heartbeat
            await websocket_manager.send_heartbeat(websocket)
            await asyncio.sleep(30)  # Heartbeat every 30 seconds
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, patient_id)


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "realtime-processing-service",
        "version": "2.0.0"
    }
    checks = {}
    all_ready = True
    
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        all_ready = False
    
    health_status["checks"] = checks
    health_status["status"] = "ready" if all_ready else "not_ready"
    
    return JSONResponse(content=health_status, status_code=200 if all_ready else 503)


@app.get("/health")
async def health():
    return await readiness()


@app.get("/metrics")
async def metrics():
    return get_metrics_response()

