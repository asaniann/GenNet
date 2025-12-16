"""
Pharmacogenomics Service
Drug-gene interactions and response prediction
"""

import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from models import (
    DrugGeneInteraction, DrugResponsePrediction,
    DrugResponseRequest, DrugResponseResponse
)
from database import get_db, init_db
from dependencies import get_current_user_id
from drug_gene_db import DrugGeneDatabase
from response_predictor import DrugResponsePredictor

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
    title="GenNet Pharmacogenomics Service",
    description="Drug-Gene Interactions and Response Prediction Service",
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
drug_gene_db = DrugGeneDatabase()
response_predictor = DrugResponsePredictor()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Pharmacogenomics Service...")
    init_db()
    logger.info("Pharmacogenomics Service started successfully")


@app.get("/drug-gene-interactions/{drug_name}")
async def get_drug_interactions(
    drug_name: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get drug-gene interactions for a drug"""
    interactions = drug_gene_db.get_interactions(drug_name)
    
    return {
        "drug_name": drug_name,
        "interactions": interactions,
        "count": len(interactions)
    }


@app.post("/drug-response/predict", response_model=DrugResponseResponse, status_code=status.HTTP_201_CREATED)
async def predict_drug_response(
    request: DrugResponseRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Predict drug response for a patient
    
    - **patient_id**: Patient ID
    - **drug_name**: Drug name
    - **drug_code**: Optional drug code
    - **indication**: Optional indication
    - **genomic_profile_id**: Optional genomic profile ID
    """
    logger.info(f"Predicting drug response for patient: {request.patient_id}, drug: {request.drug_name}")
    
    token = ""  # Would extract from request
    
    # Predict response
    prediction_data = await response_predictor.predict_response(
        request.patient_id,
        request.drug_name,
        request.genomic_profile_id,
        token
    )
    
    # Store prediction
    prediction = DrugResponsePrediction(
        id=str(uuid.uuid4()),
        patient_id=request.patient_id,
        drug_name=request.drug_name,
        drug_code=request.drug_code,
        indication=request.indication,
        response_probability=prediction_data["response_probability"],
        efficacy_score=prediction_data.get("efficacy_score"),
        toxicity_risk=prediction_data.get("toxicity_risk"),
        contributing_genes=prediction_data.get("contributing_genes"),
        contributing_variants=prediction_data.get("contributing_variants"),
        recommended_dose=prediction_data.get("recommended_dose"),
        dose_adjustment=prediction_data.get("dose_adjustment"),
        monitoring_required=prediction_data.get("monitoring_required", False),
        confidence=prediction_data["confidence"]
    )
    
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    
    return prediction


@app.get("/drug-response/{patient_id}/predictions", response_model=List[DrugResponseResponse])
async def get_patient_predictions(
    patient_id: str,
    drug_name: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get drug response predictions for a patient"""
    query = db.query(DrugResponsePrediction).filter(
        DrugResponsePrediction.patient_id == patient_id
    )
    
    if drug_name:
        query = query.filter(DrugResponsePrediction.drug_name == drug_name)
    
    predictions = query.order_by(DrugResponsePrediction.created_at.desc()).all()
    return predictions


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "pharmacogenomics-service",
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

