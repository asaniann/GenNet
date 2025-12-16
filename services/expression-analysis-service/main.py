"""
Expression Analysis Service
Signature scoring, biomarker identification, disease classification
Integrates with existing ML Service for GRN inference
"""

import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import pandas as pd

from models import (
    ExpressionProfile, SignatureScore, Biomarker,
    ExpressionProfileCreate, ExpressionProfileResponse,
    SignatureScoreRequest, SignatureScoreResponse
)
from database import get_db, init_db
from dependencies import get_current_user_id
from signature_scorer import SignatureScorer
from biomarker_finder import BiomarkerFinder
from disease_classifier import DiseaseClassifier
from s3_client import S3Client
from service_clients import MLServiceClient, GRNServiceClient, PatientDataServiceClient

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
    title="GenNet Expression Analysis Service",
    description="Expression Signature Scoring, Biomarker Identification, and Disease Classification",
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
try:
    s3_client = S3Client()
except Exception as e:
    logger.warning(f"S3 client initialization failed: {e}")
    s3_client = None

signature_scorer = SignatureScorer()
biomarker_finder = BiomarkerFinder()
disease_classifier = DiseaseClassifier()

# Service clients
ml_client = MLServiceClient()
grn_client = GRNServiceClient()
patient_client = PatientDataServiceClient()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Expression Analysis Service...")
    init_db()
    logger.info("Expression Analysis Service started successfully")


@app.post("/expression-profiles", response_model=ExpressionProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_expression_profile(
    profile: ExpressionProfileCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new expression profile"""
    logger.info(f"Creating expression profile for patient: {profile.patient_id}")
    
    db_profile = ExpressionProfile(
        id=str(uuid.uuid4()),
        patient_id=profile.patient_id,
        tissue_type=profile.tissue_type,
        platform=profile.platform,
        sample_date=profile.sample_date,
        processing_status="uploaded"
    )
    
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    return db_profile


@app.post("/expression-profiles/{profile_id}/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_expression_data(
    profile_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Upload expression data file"""
    profile = db.query(ExpressionProfile).filter(ExpressionProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("ExpressionProfile", profile_id)
    
    # Save to S3
    s3_key = f"expression-profiles/{profile_id}/{file.filename}"
    
    if s3_client:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        background_tasks.add_task(
            s3_client.s3_client.upload_file,
            tmp_path,
            s3_client.bucket_name,
            s3_key
        )
    
    profile.expression_file_s3_key = s3_key
    profile.processing_status = "uploaded"
    db.commit()
    
    # Process in background
    background_tasks.add_task(process_expression_file, profile_id, s3_key)
    
    return {
        "message": "Expression file uploaded, processing started",
        "profile_id": profile_id
    }


def process_expression_file(profile_id: str, s3_key: str):
    """Background task to process expression file"""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        profile = db.query(ExpressionProfile).filter(ExpressionProfile.id == profile_id).first()
        if not profile:
            return
        
        profile.processing_status = "processing"
        db.commit()
        
        # Download and parse expression data
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            if s3_client and s3_client.download_file(s3_key, tmp_file.name):
                # Parse CSV (genes as columns, samples as rows)
                expression_df = pd.read_csv(tmp_file.name, index_col=0)
                
                profile.gene_count = len(expression_df.columns)
                profile.sample_count = len(expression_df)
                profile.processing_status = "completed"
                profile.processed_at = datetime.utcnow()
                
                db.commit()
                logger.info(f"Processed expression data for profile {profile_id}: {len(expression_df.columns)} genes")
        
    except Exception as e:
        logger.error(f"Error processing expression file: {e}")
        profile.processing_status = "failed"
        db.commit()
    finally:
        db.close()


@app.post("/expression-profiles/{profile_id}/signatures", response_model=List[SignatureScoreResponse], status_code=status.HTTP_200_OK)
async def score_signatures(
    profile_id: str,
    request: SignatureScoreRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Score expression signatures"""
    profile = db.query(ExpressionProfile).filter(ExpressionProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("ExpressionProfile", profile_id)
    
    if not profile.expression_file_s3_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expression data not uploaded"
        )
    
    # Load expression data
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        if not s3_client or not s3_client.download_file(profile.expression_file_s3_key, tmp_file.name):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load expression data"
            )
        
        expression_df = pd.read_csv(tmp_file.name, index_col=0)
    
    # Score signatures
    results = signature_scorer.score_multiple_signatures(
        expression_df,
        request.signatures,
        request.method
    )
    
    # Store scores
    score_objects = []
    for sig_id, result in results.items():
        score = SignatureScore(
            id=str(uuid.uuid4()),
            expression_profile_id=profile_id,
            signature_id=sig_id,
            signature_name=result.get('signature_name', sig_id),
            signature_type=result.get('signature_type', 'unknown'),
            score=result.get('score', 0.0),
            percentile=result.get('percentile'),
            p_value=result.get('p_value'),
            scoring_method=request.method,
            top_genes=result.get('top_genes')
        )
        db.add(score)
        score_objects.append(score)
    
    db.commit()
    
    return score_objects


@app.post("/expression-profiles/{profile_id}/classify")
async def classify_disease(
    profile_id: str,
    disease_types: List[str],
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Classify disease from expression data"""
    profile = db.query(ExpressionProfile).filter(ExpressionProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("ExpressionProfile", profile_id)
    
    # Load expression data
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        if not s3_client or not s3_client.download_file(profile.expression_file_s3_key, tmp_file.name):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load expression data"
            )
        
        expression_df = pd.read_csv(tmp_file.name, index_col=0)
    
    # Classify
    results = disease_classifier.classify_disease(expression_df, disease_types)
    
    return results


@app.post("/expression-profiles/{profile_id}/biomarkers")
async def find_biomarkers(
    profile_id: str,
    top_n: int = 50,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Find biomarkers from expression data"""
    profile = db.query(ExpressionProfile).filter(ExpressionProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("ExpressionProfile", profile_id)
    
    # Load expression data
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        if not s3_client or not s3_client.download_file(profile.expression_file_s3_key, tmp_file.name):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load expression data"
            )
        
        expression_df = pd.read_csv(tmp_file.name, index_col=0)
    
    # Find biomarkers
    biomarkers_list = biomarker_finder.find_differential_biomarkers(expression_df, top_n=top_n)
    
    # Store biomarkers
    biomarker_objects = []
    for bm_data in biomarkers_list:
        biomarker = Biomarker(
            id=str(uuid.uuid4()),
            expression_profile_id=profile_id,
            gene=bm_data.get('gene', ''),
            expression_value=bm_data.get('mean_expression', bm_data.get('expression_value', 0.0)),
            fold_change=bm_data.get('fold_change'),
            log2_fold_change=bm_data.get('log2_fold_change'),
            p_value=bm_data.get('p_value'),
            adjusted_p_value=bm_data.get('adjusted_p_value'),
            biomarker_type="diagnostic"
        )
        db.add(biomarker)
        biomarker_objects.append(biomarker)
    
    db.commit()
    
    return biomarker_objects


@app.post("/expression-profiles/{profile_id}/infer-grn")
async def infer_grn_from_expression(
    profile_id: str,
    method: str = "GENIE3",
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Infer GRN from expression data using existing ML Service
    Integrates with ML Service for GRN inference
    """
    profile = db.query(ExpressionProfile).filter(ExpressionProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("ExpressionProfile", profile_id)
    
    if not profile.expression_file_s3_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expression data not uploaded"
        )
    
    # Call ML Service for GRN inference
    # This integrates with existing ML Service
    grn_result = await ml_client.infer_grn(
        profile.expression_file_s3_key,
        method=method
    )
    
    if grn_result:
        # Optionally store network in GRN Service
        network_id = await grn_client.create_network(
            f"GRN from expression {profile_id}",
            grn_result.get('nodes', []),
            grn_result.get('edges', []),
            user_id,
            ""  # Would need token
        )
        
        return {
            "message": "GRN inferred successfully",
            "network_id": network_id,
            "method": method,
            "edge_count": len(grn_result.get('edges', []))
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to infer GRN"
        )


@app.get("/expression-profiles/{profile_id}", response_model=ExpressionProfileResponse)
async def get_expression_profile(
    profile_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get expression profile"""
    profile = db.query(ExpressionProfile).filter(ExpressionProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("ExpressionProfile", profile_id)
    return profile


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "expression-analysis-service",
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
    
    return JSONResponse(
        content=health_status,
        status_code=200 if all_ready else 503
    )


@app.get("/health")
async def health():
    return await readiness()


@app.get("/metrics")
async def metrics():
    return get_metrics_response()

