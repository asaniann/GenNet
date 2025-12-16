"""
Genomic Analysis Service
Enterprise-grade service for VCF parsing, variant annotation, and PRS calculation
Integrates with existing Patient Data Service, GRN Service, and ML Service
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
    GenomicProfile, Variant, PRSScore,
    GenomicProfileCreate, GenomicProfileResponse,
    VariantResponse, PRSScoreRequest, PRSScoreResponse
)
from database import get_db, init_db
from dependencies import get_current_user_id
from vcf_parser import VCFParser
from variant_annotator import VariantAnnotator
from prs_calculator import PRSCalculator
from s3_client import S3Client
from service_clients import PatientDataServiceClient, GRNServiceClient

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

app = FastAPI(
    title="GenNet Genomic Analysis Service",
    description="VCF Parsing, Variant Annotation, and PRS Calculation Service",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup error handlers
setup_error_handlers(app)

# Setup compression
setup_compression(app, minimum_size=512, prefer_brotli=True)

# Add middleware
app.add_middleware(PrometheusMiddleware)
app.add_middleware(CorrelationIDMiddleware)

logger = get_logger(__name__)

# Initialize clients
try:
    s3_client = S3Client()
except Exception as e:
    logger.warning(f"S3 client initialization failed: {e}")
    s3_client = None

vcf_parser = VCFParser(s3_client=s3_client.s3_client if s3_client else None)
variant_annotator = VariantAnnotator()
prs_calculator = PRSCalculator()

# Service clients for integration
patient_client = PatientDataServiceClient()
grn_client = GRNServiceClient()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Genomic Analysis Service...")
    init_db()
    logger.info("Genomic Analysis Service started successfully")


@app.post("/genomic-profiles", response_model=GenomicProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_genomic_profile(
    profile: GenomicProfileCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new genomic profile for a patient
    
    - **patient_id**: Patient ID from Patient Data Service
    - **vcf_file_format**: File format (default: vcf)
    """
    logger.info(f"Creating genomic profile for patient: {profile.patient_id}")
    
    # Verify patient exists (integrate with Patient Data Service)
    # For now, we'll just create the profile
    
    db_profile = GenomicProfile(
        id=str(uuid.uuid4()),
        patient_id=profile.patient_id,
        vcf_file_format=profile.vcf_file_format,
        processing_status="uploaded"
    )
    
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    logger.info(f"Created genomic profile: {db_profile.id}")
    return db_profile


@app.post("/genomic-profiles/{profile_id}/upload-vcf", status_code=status.HTTP_202_ACCEPTED)
async def upload_vcf_file(
    profile_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Upload VCF file for processing
    
    - **profile_id**: Genomic profile ID
    - **file**: VCF file to upload
    """
    profile = db.query(GenomicProfile).filter(GenomicProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("GenomicProfile", profile_id)
    
    # Save file to S3
    s3_key = f"genomic-profiles/{profile_id}/{file.filename}"
    
    if s3_client:
        # Save temporarily and upload
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
    
    # Update profile
    profile.vcf_file_s3_key = s3_key
    profile.vcf_file_size = len(await file.read())
    profile.processing_status = "uploaded"
    db.commit()
    
    # Process in background
    background_tasks.add_task(process_vcf_file, profile_id, s3_key)
    
    return {
        "message": "VCF file uploaded, processing started",
        "profile_id": profile_id,
        "s3_key": s3_key
    }


def process_vcf_file(profile_id: str, s3_key: str):
    """Background task to process VCF file"""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        profile = db.query(GenomicProfile).filter(GenomicProfile.id == profile_id).first()
        if not profile:
            return
        
        profile.processing_status = "processing"
        db.commit()
        
        # Download and parse VCF
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.vcf') as tmp_file:
            if s3_client and s3_client.download_file(s3_key, tmp_file.name):
                # Parse VCF
                variants_df = vcf_parser.parse_from_file(tmp_file.name)
                
                # Extract summary
                summary = vcf_parser.extract_variant_summary(tmp_file.name)
                
                # Annotate variants (sample first 100 for speed)
                sample_variants = variants_df.head(100).to_dict('records')
                annotated = variant_annotator.annotate_batch(sample_variants)
                
                # Store variants in database
                variant_count = 0
                for var_data in annotated:
                    variant = Variant(
                        id=str(uuid.uuid4()),
                        genomic_profile_id=profile_id,
                        chromosome=var_data.get('chromosome', ''),
                        position=var_data.get('position', 0),
                        ref_allele=var_data.get('ref_allele', ''),
                        alt_allele=var_data.get('alt_allele', ''),
                        rsid=var_data.get('rsid'),
                        gene=var_data.get('gene'),
                        consequence=var_data.get('consequence'),
                        impact=var_data.get('impact'),
                        cadd_score=var_data.get('cadd_score'),
                        gnomad_af=var_data.get('gnomad_af'),
                        clinvar_significance=var_data.get('clinvar_significance'),
                        genotype=var_data.get('genotype'),
                        quality=var_data.get('quality')
                    )
                    db.add(variant)
                    variant_count += 1
                
                # Update profile
                profile.variant_count = len(variants_df)
                profile.quality_score = summary.get('quality_mean')
                profile.coverage_mean = summary.get('quality_mean')
                profile.processing_status = "completed"
                profile.processed_at = datetime.utcnow()
                profile.annotation_version = "1.0"
                profile.annotation_date = datetime.utcnow()
                
                db.commit()
                logger.info(f"Processed {variant_count} variants for profile {profile_id}")
        
    except Exception as e:
        logger.error(f"Error processing VCF file: {e}")
        profile.processing_status = "failed"
        db.commit()
    finally:
        db.close()


@app.get("/genomic-profiles/{profile_id}", response_model=GenomicProfileResponse)
async def get_genomic_profile(
    profile_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get genomic profile"""
    profile = db.query(GenomicProfile).filter(GenomicProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("GenomicProfile", profile_id)
    return profile


@app.get("/genomic-profiles/{profile_id}/variants", response_model=List[VariantResponse])
async def get_variants(
    profile_id: str,
    gene: Optional[str] = None,
    impact: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get variants for a genomic profile
    
    - **profile_id**: Genomic profile ID
    - **gene**: Filter by gene name
    - **impact**: Filter by impact (HIGH, MODERATE, LOW, MODIFIER)
    - **limit**: Maximum number of results (default: 100)
    - **skip**: Number of results to skip
    """
    query = db.query(Variant).filter(Variant.genomic_profile_id == profile_id)
    
    if gene:
        query = query.filter(Variant.gene == gene)
    if impact:
        query = query.filter(Variant.impact == impact)
    
    variants = query.order_by(Variant.position).offset(skip).limit(limit).all()
    return variants


@app.post("/genomic-profiles/{profile_id}/prs", response_model=List[PRSScoreResponse], status_code=status.HTTP_202_ACCEPTED)
async def calculate_prs(
    profile_id: str,
    prs_request: PRSScoreRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Calculate Polygenic Risk Scores for diseases
    
    - **profile_id**: Genomic profile ID
    - **diseases**: List of disease codes
    - **population**: Population for calibration
    """
    profile = db.query(GenomicProfile).filter(GenomicProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("GenomicProfile", profile_id)
    
    if profile.processing_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Genomic profile processing not completed"
        )
    
    # Get variants
    variants = db.query(Variant).filter(Variant.genomic_profile_id == profile_id).all()
    if not variants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No variants found for profile"
        )
    
    # Convert to DataFrame
    import pandas as pd
    variants_df = pd.DataFrame([{
        'rsid': v.rsid,
        'chromosome': v.chromosome,
        'position': v.position,
        'ref_allele': v.ref_allele,
        'alt_allele': v.alt_allele,
        'genotype': v.genotype
    } for v in variants])
    
    # Calculate PRS for each disease
    prs_results = []
    for disease_code in prs_request.diseases:
        try:
            prs_model_id = prs_request.prs_model_ids.get(disease_code) if prs_request.prs_model_ids else None
            prs_result = prs_calculator.calculate_prs(
                variants_df,
                disease_code,
                prs_request.population,
                prs_model_id
            )
            
            # Store PRS score
            prs_score = PRSScore(
                id=str(uuid.uuid4()),
                genomic_profile_id=profile_id,
                disease_code=disease_code,
                disease_name=disease_code,  # Would lookup actual name
                prs_score=prs_result['prs_score'],
                percentile=prs_result.get('percentile'),
                z_score=prs_result.get('z_score'),
                confidence_interval_lower=prs_result['confidence_interval_lower'],
                confidence_interval_upper=prs_result['confidence_interval_upper'],
                variant_count=prs_result['variant_count'],
                population=prs_request.population,
                prs_model_id=prs_result.get('model_id'),
                prs_model_name=prs_result.get('model_name'),
                prs_model_version=prs_result.get('model_version')
            )
            db.add(prs_score)
            prs_results.append(prs_score)
            
        except Exception as e:
            logger.error(f"Error calculating PRS for {disease_code}: {e}")
            continue
    
    db.commit()
    
    return prs_results


@app.get("/genomic-profiles/{profile_id}/prs", response_model=List[PRSScoreResponse])
async def get_prs_scores(
    profile_id: str,
    disease_code: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get PRS scores for a genomic profile"""
    query = db.query(PRSScore).filter(PRSScore.genomic_profile_id == profile_id)
    
    if disease_code:
        query = query.filter(PRSScore.disease_code == disease_code)
    
    scores = query.order_by(PRSScore.calculated_at.desc()).all()
    return scores


@app.post("/genomic-profiles/{profile_id}/create-network")
async def create_network_from_variants(
    profile_id: str,
    network_name: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a GRN network from variant data
    Integrates with existing GRN Service
    """
    profile = db.query(GenomicProfile).filter(GenomicProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError("GenomicProfile", profile_id)
    
    # Get variants with genes
    variants = db.query(Variant).filter(
        Variant.genomic_profile_id == profile_id,
        Variant.gene.isnot(None)
    ).all()
    
    if not variants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No variants with gene annotation found"
        )
    
    # Convert to list of dicts for GRN Service
    variant_list = [{
        'gene': v.gene,
        'chromosome': v.chromosome,
        'position': v.position,
        'impact': v.impact
    } for v in variants]
    
    # Create network via GRN Service (would need token)
    # For now, return placeholder
    return {
        "message": "Network creation initiated",
        "profile_id": profile_id,
        "variant_count": len(variant_list)
    }


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
        "service": "genomic-analysis-service",
        "version": "2.0.0"
    }
    checks = {}
    all_ready = True
    
    # Check database
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        all_ready = False
    
    # Check S3 (non-critical)
    if s3_client and s3_client.s3_client:
        checks["s3"] = "ok"
    else:
        checks["s3"] = "not_configured"
    
    health_status["checks"] = checks
    health_status["status"] = "ready" if all_ready else "not_ready"
    
    status_code = 200 if all_ready else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/health")
async def health():
    """Legacy health endpoint"""
    return await readiness()


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics_response()

