"""
ML/AI Service
GRN inference, parameter prediction, and pattern recognition
Enhanced to use existing inference implementations
"""

import logging
import sys
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import boto3
import tempfile

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
from shared.compression import setup_compression

# Import existing inference implementation
from inference import GRNInference
from parameter_predictor import ParameterPredictor, predict_parameters

app = FastAPI(
    title="GenNet ML Service",
    description="Machine Learning and AI Services for GRN Analysis",
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

# Initialize inference engine
grn_inference = GRNInference()


class InferenceRequest(BaseModel):
    """GRN inference request"""
    expression_data_path: str
    method: str = "GENIE3"  # ARACNE, GENIE3, GRNBoost2, PIDC, SCENIC
    parameters: Optional[Dict[str, Any]] = None


@app.post("/inference/grn")
async def infer_grn(request: InferenceRequest):
    """
    Infer GRN from expression data
    Uses existing GRNInference implementation
    """
    logger.info(f"Inferring GRN using method: {request.method}")
    
    try:
        # Load expression data from S3 or local path
        # For now, assume it's a local path or S3 key
        if request.expression_data_path.startswith("s3://") or "/" in request.expression_data_path:
            # Load from S3 or file
            s3_client = boto3.client('s3')
            bucket_name = os.getenv("S3_BUCKET_NAME", "gennet-patient-data")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                if request.expression_data_path.startswith("s3://"):
                    # Parse S3 path
                    path_parts = request.expression_data_path.replace("s3://", "").split("/", 1)
                    s3_bucket = path_parts[0]
                    s3_key = path_parts[1] if len(path_parts) > 1 else ""
                    s3_client.download_file(s3_bucket, s3_key, tmp_file.name)
                else:
                    # Local file
                    import shutil
                    shutil.copy(request.expression_data_path, tmp_file.name)
                
                # Load expression data
                expression_data = pd.read_csv(tmp_file.name, index_col=0)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid expression data path"
            )
        
        # Infer GRN based on method
        if request.method == "GENIE3":
            edges = grn_inference.infer_genie3(expression_data)
        elif request.method == "ARACNE":
            edges = grn_inference.infer_aracne(expression_data)
        elif request.method == "GRNBoost2":
            edges = grn_inference.infer_grnboost2(expression_data)
        elif request.method == "PIDC":
            edges = grn_inference.infer_pidc(expression_data)
        elif request.method == "SCENIC":
            tf_list = request.parameters.get("tf_list", []) if request.parameters else []
            edges = grn_inference.infer_scenic(expression_data, tf_list)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown inference method: {request.method}"
            )
        
        # Extract nodes from edges
        nodes = set()
        for edge in edges:
            nodes.add(edge.get("source"))
            nodes.add(edge.get("target"))
        
        nodes_list = [{"id": node, "label": node, "type": "gene"} for node in nodes]
        
        return {
            "network": {
                "nodes": nodes_list,
                "edges": edges
            },
            "method": request.method,
            "node_count": len(nodes_list),
            "edge_count": len(edges)
        }
        
    except Exception as e:
        logger.error(f"Error inferring GRN: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GRN inference failed: {str(e)}"
        )


@app.post("/prediction/parameters")
async def predict_parameters(network_id: str, expression_data: Dict[str, Any]):
    """Predict K-parameters using ML models"""
    # Placeholder - implement GNN-based parameter prediction
    return {"parameters": {}}


@app.post("/analysis/anomaly-detection")
async def detect_anomalies(network_id: str, expression_data: Dict[str, Any]):
    """Detect anomalies in network behavior"""
    # Placeholder - implement anomaly detection
    return {"anomalies": []}


@app.post("/analysis/disease-prediction")
async def predict_disease(network_id: str, expression_data: Dict[str, Any]):
    """Predict disease association"""
    # Placeholder - implement disease classification
    return {"predictions": {}}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics_response()


@app.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe"""
    return {
        "status": "ready",
        "service": "ml-service",
        "version": "1.0.0",
        "checks": {}
    }


@app.get("/health")
async def health():
    """Legacy health endpoint"""
    return await readiness()

