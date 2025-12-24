"""
Explainable AI Service
SHAP, LIME, and attention-based explanations
"""

import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import pandas as pd
import numpy as np

from models import PredictionExplanation, ExplanationRequest, ExplanationResponse
from database import get_db, init_db
from dependencies import get_current_user_id
from shap_explainer import SHAPExplainer
from lime_explainer import LIMEExplainer
from attention_visualizer import AttentionVisualizer
from nlp_explanation_generator import NLPExplanationGenerator

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
    title="GenNet Explainable AI Service",
    description="SHAP, LIME, and Attention-based Explanations",
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

# Initialize explainers
shap_explainer = SHAPExplainer()
lime_explainer = LIMEExplainer()
attention_visualizer = AttentionVisualizer()
nlp_generator = NLPExplanationGenerator()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Explainable AI Service...")
    init_db()
    logger.info("Explainable AI Service started successfully")


@app.post("/shap/explain", response_model=ExplanationResponse, status_code=status.HTTP_201_CREATED)
async def explain_with_shap(
    request: ExplanationRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Generate SHAP explanation for a prediction
    
    - **prediction_id**: Prediction ID
    - **patient_id**: Patient ID
    - **prediction_value**: Model prediction value
    - **model_type**: Model type ("ensemble", "tree", "neural", "linear")
    - **features**: Feature values used in prediction
    """
    logger.info(f"Generating SHAP explanation for prediction: {request.prediction_id}")
    
    # Convert features to DataFrame
    patient_data = pd.DataFrame([request.features])
    
    # Create model wrapper (in production, would load actual model)
    # For now, use a placeholder that returns the prediction
    class ModelWrapper:
        def __init__(self, prediction_value):
            self.prediction_value = prediction_value
        
        def predict(self, X):
            return np.array([self.prediction_value] * len(X))
    
    model = ModelWrapper(request.prediction_value)
    
    # Generate SHAP explanation
    shap_result = shap_explainer.explain_prediction(
        model=model,
        patient_data=patient_data,
        prediction=request.prediction_value,
        model_type=request.model_type
    )
    
    # Generate NLP explanation
    nlp_explanation = nlp_generator.generate_explanation(
        feature_importance=shap_result["feature_importance"],
        prediction_value=request.prediction_value,
        prediction_type="risk_score"
    )
    
    # Store explanation
    explanation = PredictionExplanation(
        id=str(uuid.uuid4()),
        prediction_id=request.prediction_id,
        patient_id=request.patient_id,
        explanation_method="shap",
        shap_values=shap_result.get("shap_values"),
        feature_importance=shap_result.get("feature_importance"),
        top_features=shap_result.get("top_features"),
        nlp_explanation=nlp_explanation,
        shap_plot_url=shap_result.get("summary_plot"),
        confidence=0.9,  # SHAP confidence
        created_at=datetime.utcnow()
    )
    
    db.add(explanation)
    db.commit()
    db.refresh(explanation)
    
    return ExplanationResponse(
        id=explanation.id,
        prediction_id=explanation.prediction_id,
        patient_id=explanation.patient_id,
        explanation_method=explanation.explanation_method,
        feature_importance=explanation.feature_importance or [],
        top_features=explanation.top_features or [],
        nlp_explanation=explanation.nlp_explanation,
        shap_plot_url=explanation.shap_plot_url,
        confidence=explanation.confidence,
        created_at=explanation.created_at
    )


@app.post("/lime/explain", response_model=ExplanationResponse, status_code=status.HTTP_201_CREATED)
async def explain_with_lime(
    request: ExplanationRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Generate LIME explanation for a prediction
    
    - **prediction_id**: Prediction ID
    - **patient_id**: Patient ID
    - **prediction_value**: Model prediction value
    - **features**: Feature values used in prediction
    - **training_data**: Optional training data for LIME
    """
    logger.info(f"Generating LIME explanation for prediction: {request.prediction_id}")
    
    # Convert features to DataFrame
    patient_data = pd.DataFrame([request.features])
    
    # Prepare training data
    if request.training_data:
        training_data = pd.DataFrame(request.training_data)
    else:
        # Use patient data as placeholder (in production, would use actual training data)
        training_data = patient_data
    
    # Create model wrapper
    class ModelWrapper:
        def __init__(self, prediction_value):
            self.prediction_value = prediction_value
        
        def predict(self, X):
            return np.array([self.prediction_value] * len(X))
    
    model = ModelWrapper(request.prediction_value)
    
    # Generate LIME explanation
    lime_result = lime_explainer.explain_prediction(
        model=model,
        patient_data=patient_data,
        training_data=training_data,
        prediction=request.prediction_value,
        num_features=10
    )
    
    # Generate NLP explanation
    nlp_explanation = nlp_generator.generate_explanation(
        feature_importance=lime_result["feature_importance"],
        prediction_value=request.prediction_value,
        prediction_type="risk_score"
    )
    
    # Store explanation
    explanation = PredictionExplanation(
        id=str(uuid.uuid4()),
        prediction_id=request.prediction_id,
        patient_id=request.patient_id,
        explanation_method="lime",
        lime_explanation=lime_result.get("explanation"),
        feature_importance=lime_result.get("feature_importance"),
        top_features=lime_result.get("top_features"),
        nlp_explanation=nlp_explanation,
        lime_plot_url=lime_result.get("visualization"),
        confidence=0.8,  # LIME confidence
        created_at=datetime.utcnow()
    )
    
    db.add(explanation)
    db.commit()
    db.refresh(explanation)
    
    return ExplanationResponse(
        id=explanation.id,
        prediction_id=explanation.prediction_id,
        patient_id=explanation.patient_id,
        explanation_method=explanation.explanation_method,
        feature_importance=explanation.feature_importance or [],
        top_features=explanation.top_features or [],
        nlp_explanation=explanation.nlp_explanation,
        lime_plot_url=explanation.lime_plot_url,
        confidence=explanation.confidence,
        created_at=explanation.created_at
    )


@app.get("/explanations/{explanation_id}", response_model=ExplanationResponse)
async def get_explanation(
    explanation_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get explanation by ID"""
    explanation = db.query(PredictionExplanation).filter(
        PredictionExplanation.id == explanation_id
    ).first()
    
    if not explanation:
        raise NotFoundError("PredictionExplanation", explanation_id)
    
    return ExplanationResponse(
        id=explanation.id,
        prediction_id=explanation.prediction_id,
        patient_id=explanation.patient_id,
        explanation_method=explanation.explanation_method,
        feature_importance=explanation.feature_importance or [],
        top_features=explanation.top_features or [],
        nlp_explanation=explanation.nlp_explanation,
        shap_plot_url=explanation.shap_plot_url,
        lime_plot_url=explanation.lime_plot_url,
        confidence=explanation.confidence,
        created_at=explanation.created_at
    )


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "explainable-ai-service",
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

