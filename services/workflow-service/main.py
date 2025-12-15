"""
Workflow Orchestrator Service
Manages analysis workflows and job execution
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

import logging
import sys
import os
from models import Workflow, WorkflowCreate, WorkflowResponse, JobStatus
from database import get_db, init_db
from workflow_engine import WorkflowEngine
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

app = FastAPI(
    title="GenNet Workflow Service",
    description="Workflow Orchestration Service",
    version="1.0.0"
)

# Add middleware (order matters: metrics first, then correlation ID)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(CorrelationIDMiddleware)

logger = get_logger(__name__)

workflow_engine = WorkflowEngine()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Workflow Service...")
    init_db()
    logger.info("Workflow Service started successfully")


@app.post("/workflows", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    workflow: WorkflowCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create and start a new workflow"""
    db_workflow = Workflow(
        id=str(uuid.uuid4()),
        name=workflow.name,
        description=workflow.description,
        workflow_type=workflow.workflow_type,
        network_id=workflow.network_id,
        parameters=workflow.parameters,
        owner_id=user_id,
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    
    # Start workflow execution
    background_tasks.add_task(workflow_engine.execute_workflow, db_workflow.id)
    
    return db_workflow


@app.get("/workflows", response_model=List[WorkflowResponse])
@cached(ttl=180, key_prefix="cache")  # Cache for 3 minutes (workflows change frequently)
async def list_workflows(
    skip: int = 0,
    limit: int = 100,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """List all workflows"""
    workflows = db.query(Workflow).filter(
        Workflow.owner_id == user_id
    ).offset(skip).limit(limit).all()
    return workflows


@app.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
@cached(ttl=60, key_prefix="cache")  # Cache for 1 minute (status changes frequently)
async def get_workflow(
    workflow_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get a specific workflow"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == user_id
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@app.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get workflow execution status"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == user_id
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"status": workflow.status, "progress": workflow.progress}


@app.get("/workflows/{workflow_id}/results")
async def get_workflow_results(
    workflow_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get workflow results"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == user_id
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Workflow not completed")
    
    return {"results": workflow.results}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics_response()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

