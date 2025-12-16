"""
Clinical Data Service
FHIR integration and clinical decision support
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
    ClinicalProfile, LabResult, ClinicalRecommendation,
    ClinicalProfileCreate, ClinicalProfileResponse,
    LabResultCreate, LabResultResponse
)
from database import get_db, init_db
from dependencies import get_current_user_id
from fhir_client import FHIRClient
from decision_support import ClinicalDecisionSupport

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
    title="GenNet Clinical Data Service",
    description="FHIR Integration and Clinical Decision Support Service",
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
fhir_client = FHIRClient()
decision_support = ClinicalDecisionSupport()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Clinical Data Service...")
    init_db()
    logger.info("Clinical Data Service started successfully")


@app.post("/clinical-profiles", response_model=ClinicalProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_clinical_profile(
    profile: ClinicalProfileCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new clinical profile"""
    logger.info(f"Creating clinical profile for patient: {profile.patient_id}")
    
    db_profile = ClinicalProfile(
        id=str(uuid.uuid4()),
        patient_id=profile.patient_id,
        age=profile.age,
        sex=profile.sex,
        ethnicity=profile.ethnicity,
        medical_history=profile.medical_history,
        family_history=profile.family_history,
        medications=profile.medications
    )
    
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    return db_profile


@app.get("/clinical-profiles/{profile_id}", response_model=ClinicalProfileResponse)
async def get_clinical_profile(
    profile_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get clinical profile"""
    profile = db.query(ClinicalProfile).filter(ClinicalProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("ClinicalProfile", profile_id)
    return profile


@app.post("/clinical-profiles/{profile_id}/sync-fhir")
async def sync_from_fhir(
    profile_id: str,
    fhir_patient_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Sync clinical data from FHIR server"""
    profile = db.query(ClinicalProfile).filter(ClinicalProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("ClinicalProfile", profile_id)
    
    # Fetch from FHIR
    fhir_patient = fhir_client.get_patient(fhir_patient_id)
    observations = fhir_client.get_observations(fhir_patient_id)
    conditions = fhir_client.get_conditions(fhir_patient_id)
    medications = fhir_client.get_medications(fhir_patient_id)
    
    # Update profile
    if fhir_patient:
        profile.fhir_patient_id = fhir_patient_id
        if fhir_patient.get("birth_date"):
            # Calculate age from birth date
            try:
                from dateutil.parser import parse
                birth_date = parse(fhir_patient["birth_date"])
                age = (datetime.now() - birth_date.replace(tzinfo=None)).days // 365
                profile.age = age
            except:
                # If parsing fails, skip age calculation
                pass
        profile.sex = fhir_patient.get("gender")
    
    # Store lab results
    for obs in observations:
        if obs.get("code", {}).get("code"):
            lab_result = LabResult(
                id=str(uuid.uuid4()),
                patient_id=profile.patient_id,
                clinical_profile_id=profile_id,
                test_name=obs.get("code", {}).get("display", ""),
                test_code=obs.get("code", {}).get("code"),
                test_date=datetime.utcnow(),
                value=obs.get("value"),
                unit=obs.get("unit"),
                fhir_observation_id=obs.get("id")
            )
            db.add(lab_result)
    
    # Update medical history from conditions
    if conditions:
        condition_names = [c.get("code", {}).get("display", "") for c in conditions]
        profile.medical_history = condition_names
    
    # Update medications
    if medications:
        med_names = [m.get("medication", {}).get("display", "") for m in medications]
        profile.medications = med_names
    
    db.commit()
    
    return {
        "message": "FHIR sync completed",
        "observations_synced": len(observations),
        "conditions_synced": len(conditions),
        "medications_synced": len(medications)
    }


@app.post("/lab-results", response_model=LabResultResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_result(
    lab_result: LabResultCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new lab result"""
    db_result = LabResult(
        id=str(uuid.uuid4()),
        patient_id=lab_result.patient_id,
        test_name=lab_result.test_name,
        test_code=lab_result.test_code,
        test_date=lab_result.test_date,
        value=lab_result.value,
        unit=lab_result.unit,
        reference_range=lab_result.reference_range,
        interpretation=lab_result.interpretation
    )
    
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    return db_result


@app.get("/clinical-profiles/{profile_id}/recommendations", response_model=List[Dict])
async def get_recommendations(
    profile_id: str,
    genomic_risk: Optional[float] = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get clinical decision support recommendations"""
    profile = db.query(ClinicalProfile).filter(ClinicalProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("ClinicalProfile", profile_id)
    
    # Get lab results
    lab_results = db.query(LabResult).filter(
        LabResult.patient_id == profile.patient_id
    ).all()
    
    lab_results_dict = [{
        "test_name": lr.test_name,
        "value": lr.value,
        "interpretation": lr.interpretation
    } for lr in lab_results]
    
    # Generate recommendations
    profile_dict = {
        "age": profile.age,
        "sex": profile.sex,
        "medications": profile.medications or []
    }
    
    recommendations = decision_support.generate_recommendations(
        profile_dict,
        lab_results_dict,
        genomic_risk
    )
    
    # Store recommendations
    for rec in recommendations:
        db_rec = ClinicalRecommendation(
            id=str(uuid.uuid4()),
            patient_id=profile.patient_id,
            recommendation_type=rec["type"],
            title=rec["title"],
            description=rec["description"],
            priority=rec.get("priority", "medium"),
            evidence_level=rec.get("evidence_level"),
            guideline_reference=rec.get("guideline_reference"),
            action_items=rec.get("action_items")
        )
        db.add(db_rec)
    
    db.commit()
    
    return recommendations


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "clinical-data-service",
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

