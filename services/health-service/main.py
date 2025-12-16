"""
Health Service
Unified health reports and recommendations
Integrates with all analysis services
"""

import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta

from models import HealthReport, HealthRecommendation, HealthReportRequest, HealthReportResponse
from database import get_db, init_db
from dependencies import get_current_user_id
from recommendation_engine import RecommendationEngine
from report_generator import ReportGenerator
from service_clients import AnalysisServiceClient

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
    title="GenNet Health Service",
    description="Unified Health Reports and Recommendations Service",
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
recommendation_engine = RecommendationEngine()
report_generator = ReportGenerator()
analysis_client = AnalysisServiceClient()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Health Service...")
    init_db()
    logger.info("Health Service started successfully")


@app.post("/health/{patient_id}/reports", response_model=HealthReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_health_report(
    patient_id: str,
    request: HealthReportRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive health report
    
    - **patient_id**: Patient ID
    - **report_type**: Type of report (comprehensive, disease_risk, drug_response)
    - **format**: Output format (pdf, json, html)
    """
    logger.info(f"Generating health report for patient: {patient_id}")
    
    token = ""  # Would extract from request
    
    # Get predictions from all services
    predictions = await analysis_client.get_all_predictions(
        patient_id,
        "ICD10:C50",  # Would be parameter
        token
    )
    
    # Generate recommendations
    recommendations = recommendation_engine.generate_recommendations(
        predictions,
        {"age_range": "40-50"}  # Would get from patient data
    )
    
    # Create report record
    report = HealthReport(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        report_type=request.report_type,
        format=request.format,
        predictions_summary=predictions,
        recommendations=recommendations,
        expires_at=datetime.utcnow() + timedelta(days=90)  # 90-day expiration
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Generate report file in background
    background_tasks.add_task(
        generate_report_file,
        report.id,
        patient_id,
        predictions,
        recommendations,
        request.format
    )
    
    return report


def generate_report_file(
    report_id: str,
    patient_id: str,
    predictions: Dict,
    recommendations: List[Dict],
    format: str
):
    """Background task to generate report file"""
    from database import SessionLocal
    from s3_client import S3Client
    
    db = SessionLocal()
    try:
        report = db.query(HealthReport).filter(HealthReport.id == report_id).first()
        if not report:
            return
        
        s3_client = S3Client()
        import tempfile
        
        if format == "pdf":
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                if report_generator.generate_pdf_report(patient_id, predictions, recommendations, tmp_file.name):
                    s3_key = f"health-reports/{report_id}/report.pdf"
                    s3_client.s3_client.upload_file(tmp_file.name, s3_client.bucket_name, s3_key)
                    report.report_file_s3_key = s3_key
        elif format == "json":
            json_data = report_generator.generate_json_report(patient_id, predictions, recommendations)
            import json as json_lib
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
                json_lib.dump(json_data, tmp_file)
                s3_key = f"health-reports/{report_id}/report.json"
                s3_client.s3_client.upload_file(tmp_file.name, s3_client.bucket_name, s3_key)
                report.report_file_s3_key = s3_key
        elif format == "html":
            html_content = report_generator.generate_html_report(patient_id, predictions, recommendations)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as tmp_file:
                tmp_file.write(html_content)
                s3_key = f"health-reports/{report_id}/report.html"
                s3_client.s3_client.upload_file(tmp_file.name, s3_client.bucket_name, s3_key)
                report.report_file_s3_key = s3_key
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error generating report file: {e}")
    finally:
        db.close()


@app.get("/health/{patient_id}/predictions/comprehensive")
async def get_comprehensive_predictions(
    patient_id: str,
    disease_code: str = "ICD10:C50",
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get comprehensive predictions from all methods"""
    token = ""  # Would extract
    
    predictions = await analysis_client.get_all_predictions(patient_id, disease_code, token)
    
    return {
        "patient_id": patient_id,
        "disease_code": disease_code,
        "predictions": predictions,
        "summary": "Comprehensive health predictions from multiple analysis methods"
    }


@app.get("/health/{patient_id}/recommendations", response_model=List[Dict])
async def get_recommendations(
    patient_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get health recommendations for patient"""
    recommendations = db.query(HealthRecommendation).filter(
        HealthRecommendation.patient_id == patient_id
    ).order_by(HealthRecommendation.created_at.desc()).all()
    
    return [{
        "id": rec.id,
        "type": rec.recommendation_type,
        "title": rec.title,
        "description": rec.description,
        "priority": rec.priority,
        "evidence_level": rec.evidence_level
    } for rec in recommendations]


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "health-service",
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

