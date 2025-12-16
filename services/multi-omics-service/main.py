"""
Multi-Omics Integration Service
Fuses multiple omics data types for comprehensive analysis
"""

import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from models import MultiOmicsProfile, MultiOmicsIntegrationRequest, MultiOmicsProfileResponse
from database import get_db, init_db
from dependencies import get_current_user_id
from data_fusion import DataFusion

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
    title="GenNet Multi-Omics Service",
    description="Multi-Omics Data Integration and Fusion Service",
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
data_fusion = DataFusion()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Multi-Omics Service...")
    init_db()
    logger.info("Multi-Omics Service started successfully")


@app.post("/multi-omics/integrate", response_model=MultiOmicsProfileResponse, status_code=status.HTTP_201_CREATED)
async def integrate_omics_data(
    request: MultiOmicsIntegrationRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Integrate multiple omics data types
    
    - **patient_id**: Patient ID
    - **genomic_profile_id**: Optional genomic profile ID
    - **expression_profile_id**: Optional expression profile ID
    - **fusion_method**: Fusion method (early, late, intermediate, multi_view)
    """
    logger.info(f"Integrating multi-omics data for patient: {request.patient_id}")
    
    # Count available omics
    omics_count = sum([
        request.genomic_profile_id is not None,
        request.expression_profile_id is not None,
        request.proteomic_profile_id is not None,
        request.metabolomic_profile_id is not None
    ])
    
    if omics_count < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 omics data types required for multi-omics integration"
        )
    
    # Create multi-omics profile
    profile = MultiOmicsProfile(
        id=str(uuid.uuid4()),
        patient_id=request.patient_id,
        genomic_profile_id=request.genomic_profile_id,
        expression_profile_id=request.expression_profile_id,
        proteomic_profile_id=request.proteomic_profile_id,
        metabolomic_profile_id=request.metabolomic_profile_id,
        fusion_method=request.fusion_method,
        omics_count=omics_count
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile


@app.post("/multi-omics/{profile_id}/predict")
async def predict_from_multi_omics(
    profile_id: str,
    disease_code: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Predict disease risk from multi-omics profile"""
    profile = db.query(MultiOmicsProfile).filter(MultiOmicsProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("MultiOmicsProfile", profile_id)
    
    # Placeholder - would load actual data and make prediction
    return {
        "profile_id": profile_id,
        "disease_code": disease_code,
        "risk_score": 75.5,
        "confidence": 0.88,
        "method": "multi_omics",
        "fusion_method": profile.fusion_method
    }


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "multi-omics-service",
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

