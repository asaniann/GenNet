"""
Patient Data Service - Unified patient data management
Enterprise-grade service with privacy controls and data management
"""

import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from models import (
    Patient, PatientCreate, PatientUpdate, PatientResponse,
    DataUploadRequest, DataUploadResponse
)
from database import get_db, init_db
from dependencies import get_current_user_id, verify_patient_access
from s3_client import S3Client

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
from shared.error_handler import setup_error_handlers
from shared.exceptions import NotFoundError, ValidationError
from shared.compression import setup_compression
from shared.api_versioning import APIVersion, get_api_version, require_version

app = FastAPI(
    title="GenNet Patient Data Service",
    description="Unified Patient Data Management Service with Privacy Controls",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup error handlers
setup_error_handlers(app)

# Setup compression
setup_compression(app, minimum_size=512, prefer_brotli=True)

# Add middleware (order matters: metrics first, then correlation ID, then compression)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(CorrelationIDMiddleware)

logger = get_logger(__name__)

# Initialize S3 client
try:
    s3_client = S3Client()
except Exception as e:
    logger.warning(f"S3 client initialization failed: {e}")
    s3_client = None


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Patient Data Service...")
    init_db()
    logger.info("Patient Data Service started successfully")


def generate_anonymized_id() -> str:
    """Generate anonymized patient ID"""
    return f"PAT-{uuid.uuid4().hex[:12].upper()}"


@app.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
@require_version(APIVersion.V2)
async def create_patient(
    patient: PatientCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new patient record
    
    - **user_id**: User ID from auth service (automatically extracted from token)
    - **age_range**: Age range (e.g., "40-50")
    - **gender**: Gender
    - **ethnicity**: Ethnicity
    - **consent_given**: Consent for data processing
    - **data_retention_policy**: Data retention policy
    """
    logger.info(f"Creating patient for user_id: {user_id}")
    
    # Verify user_id matches token
    if patient.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create patient for different user"
        )
    
    # Generate anonymized ID
    anonymized_id = generate_anonymized_id()
    
    # Create patient record
    db_patient = Patient(
        id=str(uuid.uuid4()),
        user_id=user_id,
        anonymized_id=anonymized_id,
        age_range=patient.age_range,
        gender=patient.gender,
        ethnicity=patient.ethnicity,
        consent_given=patient.consent_given,
        consent_date=datetime.utcnow() if patient.consent_given else None,
        data_retention_policy=patient.data_retention_policy
    )
    
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    logger.info(f"Created patient: {db_patient.id} (anonymized: {anonymized_id})")
    return db_patient


@app.get("/patients", response_model=List[PatientResponse])
@require_version(APIVersion.V2)
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all patients for the current user with advanced search and filtering
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (max 100)
    - **search**: Full-text search term
    - **sort_by**: Field to sort by
    - **sort_order**: Sort order ("asc" or "desc")
    """
    if limit > 100:
        limit = 100
    
    from shared.search import AdvancedSearch
    
    query = db.query(Patient).filter(
        Patient.user_id == user_id,
        Patient.deleted_at.is_(None)  # Not soft-deleted
    )
    
    # Apply search
    if search:
        search_fields = ["anonymized_id", "age_range", "gender", "ethnicity"]
        query = AdvancedSearch.apply_search(query, Patient, search, search_fields)
    
    # Apply sorting
    if sort_by:
        query = AdvancedSearch.apply_sorting(query, Patient, sort_by, sort_order)
    else:
        query = query.order_by(Patient.created_at.desc())
    
    # Apply pagination
    patients = query.offset(skip).limit(limit).all()
    
    return patients


@app.get("/patients/{patient_id}", response_model=PatientResponse)
@require_version(APIVersion.V2)
async def get_patient(
    patient_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get a specific patient by ID
    
    - **patient_id**: Patient UUID
    """
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.user_id == user_id,
        Patient.deleted_at.is_(None)
    ).first()
    
    if not patient:
        raise NotFoundError("Patient", patient_id)
    
    return patient


@app.put("/patients/{patient_id}", response_model=PatientResponse)
@require_version(APIVersion.V2)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update a patient record
    
    - **patient_id**: Patient UUID
    - Updates only provided fields
    """
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.user_id == user_id,
        Patient.deleted_at.is_(None)
    ).first()
    
    if not patient:
        raise NotFoundError("Patient", patient_id)
    
    # Update fields
    update_data = patient_update.dict(exclude_unset=True)
    if update_data:
        for field, value in update_data.items():
            setattr(patient, field, value)
        
        # Update consent_date if consent_given changed
        if "consent_given" in update_data and update_data["consent_given"]:
            patient.consent_date = datetime.utcnow()
        
        patient.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(patient)
    
    return patient


@app.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_version(APIVersion.V2)
async def delete_patient(
    patient_id: str,
    hard_delete: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a patient record (soft delete by default)
    
    - **patient_id**: Patient UUID
    - **hard_delete**: If True, permanently delete (default: False, soft delete)
    """
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.user_id == user_id
    ).first()
    
    if not patient:
        raise NotFoundError("Patient", patient_id)
    
    if hard_delete:
        db.delete(patient)
    else:
        # Soft delete
        patient.deleted_at = datetime.utcnow()
    
    db.commit()
    return None


@app.post("/patients/{patient_id}/data/upload", response_model=DataUploadResponse, status_code=status.HTTP_202_ACCEPTED)
@require_version(APIVersion.V2)
async def upload_patient_data(
    patient_id: str,
    file: UploadFile = File(...),
    data_type: str = None,
    file_format: str = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Upload patient data file
    
    - **patient_id**: Patient UUID
    - **file**: Data file to upload
    - **data_type**: Type of data (genomic, expression, clinical, etc.)
    - **file_format**: File format (vcf, csv, tsv, json, etc.)
    """
    # Verify patient access
    await verify_patient_access(patient_id, user_id, db)
    
    # Generate upload ID and S3 key
    upload_id = str(uuid.uuid4())
    s3_key = f"patients/{patient_id}/{data_type}/{upload_id}.{file_format}"
    
    # Save file temporarily
    temp_path = f"/tmp/{upload_id}"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Upload to S3 in background
    if s3_client:
        background_tasks.add_task(
            s3_client.upload_file,
            temp_path,
            s3_key,
            metadata={
                "patient_id": patient_id,
                "data_type": data_type,
                "file_format": file_format,
                "original_filename": file.filename
            }
        )
    
    # Update patient data flags
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if data_type == "genomic":
        patient.has_genomic_data = True
    elif data_type == "expression":
        patient.has_expression_data = True
    elif data_type == "clinical":
        patient.has_clinical_data = True
    
    if patient.has_genomic_data and patient.has_expression_data:
        patient.has_multi_omics = True
    
    db.commit()
    
    # Publish event to Kafka for real-time processing
    try:
        from shared.kafka_publisher import KafkaEventPublisher
        KafkaEventPublisher.publish_event(
            topic="patient-events",
            event={
                "patient_id": patient_id,
                "event_type": "data_upload",
                "event_data": {
                    "upload_id": upload_id,
                    "data_type": data_type,
                    "file_format": file_format,
                    "s3_key": s3_key
                }
            },
            key=patient_id
        )
    except Exception as e:
        logger.warning(f"Could not publish event to Kafka: {e}")
    
    return DataUploadResponse(
        upload_id=upload_id,
        patient_id=patient_id,
        data_type=data_type or "unknown",
        s3_key=s3_key,
        processing_status="uploaded",
        estimated_completion=None
    )


@app.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe"""
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "patient-data-service",
        "version": "2.0.0"
    }
    checks = {}
    all_ready = True
    
    # Check database connection
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        all_ready = False
    
    # Check S3 connection (non-critical)
    if s3_client and s3_client.s3_client:
        checks["s3"] = "ok"
    else:
        checks["s3"] = "not_configured"
    
    health_status["checks"] = checks
    health_status["status"] = "ready" if all_ready else "not_ready"
    
    status_code = 200 if all_ready else 503
    return JSONResponse(content=health_status, status_code=status_code)


# Include GDPR data subject rights router
try:
    from data_subject_rights import router as gdpr_router
    app.include_router(gdpr_router)
    logger.info("GDPR data subject rights router included")
except ImportError as e:
    logger.warning(f"GDPR router not available: {e}")


@app.get("/health")
async def health():
    """Legacy health endpoint"""
    return await readiness()


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics_response()

