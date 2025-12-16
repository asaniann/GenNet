"""
Analysis Router Service
Intelligent routing and method selection
Integrates with all analysis services
"""

import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from models import AnalysisPlan, AnalysisRequest, AnalysisPlanResponse
from database import get_db, init_db
from dependencies import get_current_user_id
from data_assessor import DataAssessor
from method_selector import MethodSelector

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
    title="GenNet Analysis Router Service",
    description="Intelligent Analysis Method Selection and Routing",
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
data_assessor = DataAssessor()
method_selector = MethodSelector()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Analysis Router Service...")
    init_db()
    logger.info("Analysis Router Service started successfully")


@app.post("/analyze/request", response_model=AnalysisPlanResponse, status_code=status.HTTP_201_CREATED)
async def request_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Request analysis for a patient
    Intelligently selects methods based on available data
    """
    logger.info(f"Requesting analysis for patient: {request.patient_id}")
    
    # Get auth token (would be extracted from request)
    token = ""  # Would extract from headers
    
    # Assess available data
    assessment = await data_assessor.assess_patient_data(request.patient_id, token)
    
    # Select methods
    selection = method_selector.select_methods(assessment, request.preferences)
    
    # Create analysis plan
    plan = AnalysisPlan(
        id=str(uuid.uuid4()),
        patient_id=request.patient_id,
        methods=selection["methods"],
        ensemble_strategy=selection["ensemble_strategy"],
        grn_feasible=selection["grn_feasible"],
        grn_feasibility_reason=selection.get("grn_feasibility_reason"),
        has_genomic_data=assessment.get("has_genomic_data", False),
        has_expression_data=assessment.get("has_expression_data", False),
        has_clinical_data=assessment.get("has_clinical_data", False),
        has_multi_omics=assessment.get("has_multi_omics", False),
        status="planned"
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    # Execute analysis in background
    background_tasks.add_task(execute_analysis_plan, plan.id)
    
    return plan


def execute_analysis_plan(plan_id: str):
    """Background task to execute analysis plan"""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        plan = db.query(AnalysisPlan).filter(AnalysisPlan.id == plan_id).first()
        if not plan:
            return
        
        plan.status = "executing"
        plan.started_at = datetime.utcnow()
        db.commit()
        
        # Route to appropriate services based on methods
        # This would coordinate with all analysis services
        # For now, just mark as completed
        
        plan.status = "completed"
        plan.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"Error executing analysis plan: {e}")
        plan.status = "failed"
        db.commit()
    finally:
        db.close()


@app.get("/analysis-plans/{plan_id}", response_model=AnalysisPlanResponse)
async def get_analysis_plan(
    plan_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get analysis plan"""
    plan = db.query(AnalysisPlan).filter(AnalysisPlan.id == plan_id).first()
    if not plan:
        raise NotFoundError("AnalysisPlan", plan_id)
    return plan


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "analysis-router-service",
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

