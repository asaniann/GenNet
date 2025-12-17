"""
Qualitative Modeling Service
SMBioNet integration for CTL verification and parameter generation
"""

import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pydantic import Field, validator
import uuid

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
from shared.exceptions import ValidationError, NotFoundError
from smbionet_integration import SMBioNetIntegration
from state_graph import StateGraphGenerator

app = FastAPI(
    title="GenNet Qualitative Service",
    description="Qualitative Modeling and SMBioNet Integration",
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
smbionet = SMBioNetIntegration()
state_graph_gen = StateGraphGenerator()


class CTLFormula(BaseModel):
    """CTL formula model"""
    formula: str = Field(..., min_length=1, max_length=1000, description="CTL formula string")
    description: Optional[str] = Field(None, max_length=500, description="Optional description of the formula")
    
    @validator('formula')
    def validate_formula(cls, v: str) -> str:
        """Validate formula is not empty"""
        if not v or not v.strip():
            raise ValueError("Formula cannot be empty")
        return v.strip()


class ParameterSet(BaseModel):
    """Parameter set model"""
    parameters: Dict[str, Any] = Field(..., description="Parameter values")
    network_id: str = Field(..., min_length=1, description="Network identifier")
    
    @validator('network_id')
    def validate_network_id(cls, v: str) -> str:
        """Validate network ID is not empty"""
        if not v or not v.strip():
            raise ValueError("Network ID cannot be empty")
        return v.strip()


@app.post("/ctl/verify")
async def verify_ctl(formula: CTLFormula):
    """
    Verify CTL formula syntax and semantics
    
    - **formula**: CTL formula string (e.g., "AG(p -> AF q)")
    - **description**: Optional description of the formula
    """
    logger.info(f"Verifying CTL formula: {formula.formula}")
    
    try:
        result = smbionet.verify_ctl(formula.formula)
        
        return {
            "valid": result["valid"],
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
            "formula": formula.formula,
            "description": formula.description,
            "parsed_structure": result.get("parsed_structure")
        }
    except Exception as e:
        logger.error(f"Error verifying CTL formula: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"CTL verification failed: {str(e)}"
        )


@app.post("/parameters/generate")
async def generate_parameters(
    network_id: str,
    ctl_formula: CTLFormula,
    network_structure: Optional[Dict[str, Any]] = None
):
    """
    Generate K-parameters from CTL formula and network structure
    
    - **network_id**: Network identifier
    - **ctl_formula**: CTL formula to use for parameter generation
    - **network_structure**: Optional network structure (nodes, edges)
    """
    logger.info(f"Generating parameters for network: {network_id}")
    
    try:
        # Verify formula first
        verification = smbionet.verify_ctl(ctl_formula.formula)
        if not verification["valid"]:
            raise ValidationError(f"Invalid CTL formula: {verification['errors']}")
        
        # Generate parameters
        result = smbionet.generate_parameters(
            network_id=network_id,
            ctl_formula=ctl_formula.formula,
            network_structure=network_structure
        )
        
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating parameters: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Parameter generation failed: {str(e)}"
        )


@app.post("/parameters/filter")
async def filter_parameters(
    parameter_sets: List[Dict],
    constraints: Dict[str, Any]
):
    """
    Filter parameter sets based on constraints
    
    - **parameter_sets**: List of parameter sets to filter
    - **constraints**: Filtering constraints (node_ids, k_value_range, threshold_range)
    """
    logger.info(f"Filtering {len(parameter_sets)} parameter sets")
    
    try:
        result = smbionet.filter_parameters(parameter_sets, constraints)
        return result
    except Exception as e:
        logger.error(f"Error filtering parameters: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Parameter filtering failed: {str(e)}"
        )


@app.post("/state-graph/generate")
async def generate_state_graph(
    network_id: str,
    parameters: Dict[str, Any],
    network_structure: Optional[Dict[str, Any]] = None
):
    """
    Generate state graph from parameters
    
    - **network_id**: Network identifier
    - **parameters**: K-parameters for the network
    - **network_structure**: Optional network structure (nodes, edges)
    """
    logger.info(f"Generating state graph for network: {network_id}")
    
    try:
        result = state_graph_gen.generate_state_graph(
            network_id=network_id,
            parameters=parameters,
            network_structure=network_structure
        )
        return result
    except Exception as e:
        logger.error(f"Error generating state graph: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"State graph generation failed: {str(e)}"
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
        "service": "qualitative-service",
        "version": "1.0.0",
        "checks": {}
    }


@app.get("/health")
async def health():
    """Legacy health endpoint"""
    return await readiness()

