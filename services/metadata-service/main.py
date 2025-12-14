"""
Metadata Service
Data catalog and metadata management
"""

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from models import MetadataEntry
from database import get_db, init_db

# Import shared middleware and utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.metrics import PrometheusMiddleware, get_metrics_response
from shared.cache import cached
app = FastAPI(
    title="GenNet Metadata Service",
    description="Metadata and Data Catalog Service",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Metadata Service...")
    init_db()
    logger.info("Metadata Service started successfully")


@app.get("/metadata")
@cached(ttl=300, key_prefix="cache")  # Cache for 5 minutes
async def list_metadata(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List metadata entries"""
    entries = db.query(MetadataEntry).offset(skip).limit(limit).all()
    return entries


@app.get("/metadata/{entry_id}")
@cached(ttl=600, key_prefix="cache")  # Cache for 10 minutes
async def get_metadata(entry_id: str, db: Session = Depends(get_db)):
    """Get specific metadata entry"""
    entry = db.query(MetadataEntry).filter(MetadataEntry.id == entry_id).first()
    if not entry:
        return {"error": "Not found"}
    return entry


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics_response()


@app.get("/health")
async def health():
    return {"status": "healthy"}

