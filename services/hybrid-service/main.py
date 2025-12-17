"""
Hybrid Modeling Service
HyTech integration for time delay computation
"""

import logging
import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import correlation ID middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.logging_middleware import CorrelationIDMiddleware, get_logger
from shared.metrics import PrometheusMiddleware, get_metrics_response
from shared.error_handler import setup_error_handlers
from shared.exceptions import ValidationError
from hytech_integration import HyTechIntegration

app = FastAPI(
    title="GenNet Hybrid Service",
    description="Hybrid Modeling and HyTech Integration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup error handlers
setup_error_handlers(app)

# Add correlation ID middleware
# Add middleware (order matters: metrics first, then correlation ID)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(CorrelationIDMiddleware)

logger = get_logger(__name__)

# Initialize components
hytech = HyTechIntegration()


class HybridModel(BaseModel):
    """Hybrid model specification"""
    network_id: str
    parameters: Dict[str, Any]
    time_constraints: Dict[str, float]


@app.post("/time-delays/compute")
async def compute_time_delays(
    model: HybridModel,
    network_structure: Optional[Dict[str, Any]] = None
):
    """
    Compute time delays for hybrid automata
    
    - **network_id**: Network identifier
    - **parameters**: Model parameters
    - **time_constraints**: Time constraints for transitions
    - **network_structure**: Optional network structure (nodes, edges)
    """
    logger.info(f"Computing time delays for network: {model.network_id}")
    
    try:
        result = hytech.compute_time_delays(
            network_id=model.network_id,
            parameters=model.parameters,
            time_constraints=model.time_constraints,
            network_structure=network_structure
        )
        return result
    except Exception as e:
        logger.error(f"Error computing time delays: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Time delay computation failed: {str(e)}"
        )


@app.post("/trajectory/analyze")
async def analyze_trajectory(
    model: HybridModel,
    initial_state: Dict[str, float],
    time_horizon: float = 10.0,
    time_step: float = 0.1,
    network_structure: Optional[Dict[str, Any]] = None
):
    """
    Analyze hybrid automata trajectories
    
    - **network_id**: Network identifier
    - **parameters**: Model parameters
    - **initial_state**: Initial state values
    - **time_horizon**: Time horizon for simulation (default: 10.0)
    - **time_step**: Time step for simulation (default: 0.1)
    - **network_structure**: Optional network structure
    """
    logger.info(f"Analyzing trajectory for network: {model.network_id}")
    
    try:
        result = hytech.analyze_trajectory(
            network_id=model.network_id,
            parameters=model.parameters,
            initial_state=initial_state,
            time_horizon=time_horizon,
            time_step=time_step,
            network_structure=network_structure
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing trajectory: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Trajectory analysis failed: {str(e)}"
        )


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
        "service": "hybrid-service",
        "version": "1.0.0",
        "checks": {}
    }


@app.get("/health")
async def health():
    """Legacy health endpoint"""
    return await readiness()

