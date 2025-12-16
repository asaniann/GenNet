"""
Ensemble Service
Combines predictions from multiple analysis methods
"""

import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from models import EnsemblePrediction, EnsembleRequest, EnsembleResponse
from database import get_db, init_db
from dependencies import get_current_user_id
from ensemble_predictor import EnsemblePredictor

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
    title="GenNet Ensemble Service",
    description="Ensemble Prediction Service - Combining Multiple Analysis Methods",
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

# Initialize ensemble predictor
ensemble_predictor = EnsemblePredictor()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Ensemble Service...")
    init_db()
    logger.info("Ensemble Service started successfully")


@app.post("/ensemble/predict", response_model=EnsembleResponse, status_code=status.HTTP_201_CREATED)
async def create_ensemble_prediction(
    request: EnsembleRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create ensemble prediction from multiple method predictions
    
    - **analysis_plan_id**: Analysis plan ID
    - **disease_code**: Disease code
    - **component_predictions**: List of predictions from different methods
    """
    logger.info(f"Creating ensemble prediction for disease: {request.disease_code}")
    
    if not request.component_predictions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No component predictions provided"
        )
    
    # Determine ensemble strategy from first prediction or use default
    strategy = request.component_predictions[0].get("ensemble_strategy", "weighted_voting")
    
    # Create ensemble prediction
    if strategy == "weighted_voting":
        result = ensemble_predictor.predict_weighted_voting(request.component_predictions)
    elif strategy == "stacking":
        result = ensemble_predictor.predict_stacking(request.component_predictions)
    elif strategy == "bayesian_averaging":
        result = ensemble_predictor.predict_bayesian_averaging(request.component_predictions)
    else:
        # Default to weighted voting
        result = ensemble_predictor.predict_weighted_voting(request.component_predictions)
    
    # Aggregate evidence
    evidence = ensemble_predictor.aggregate_evidence(request.component_predictions)
    
    # Store ensemble prediction
    ensemble = EnsemblePrediction(
        id=str(uuid.uuid4()),
        analysis_plan_id=request.analysis_plan_id,
        patient_id=request.component_predictions[0].get("patient_id", ""),
        ensemble_strategy=result["ensemble_strategy"],
        component_prediction_ids=[p.get("id", "") for p in request.component_predictions],
        disease_code=request.disease_code,
        disease_name=request.disease_code,  # Would lookup actual name
        risk_score=result["risk_score"],
        confidence=result["confidence"],
        method_contributions=result.get("method_contributions"),
        method_weights=result.get("method_weights"),
        agreement_score=result.get("agreement_score"),
        evidence_summary=evidence
    )
    
    db.add(ensemble)
    db.commit()
    db.refresh(ensemble)
    
    return ensemble


@app.get("/ensemble/{ensemble_id}", response_model=EnsembleResponse)
async def get_ensemble_prediction(
    ensemble_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get ensemble prediction"""
    ensemble = db.query(EnsemblePrediction).filter(EnsemblePrediction.id == ensemble_id).first()
    if not ensemble:
        raise NotFoundError("EnsemblePrediction", ensemble_id)
    return ensemble


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "ensemble-service",
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

