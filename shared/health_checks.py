"""
Shared health check utilities
"""
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional


def create_liveness_response() -> JSONResponse:
    """Create a simple liveness probe response"""
    return JSONResponse(
        content={"status": "alive"},
        status_code=200
    )


def create_readiness_response(
    service_name: str,
    version: str,
    checks: Dict[str, str],
    all_ready: bool = True
) -> JSONResponse:
    """Create a readiness probe response with dependency checks"""
    status = "ready" if all_ready else "not_ready"
    status_code = 200 if all_ready else 503
    
    response = {
        "status": status,
        "service": service_name,
        "version": version,
        "checks": checks
    }
    
    return JSONResponse(
        content=response,
        status_code=status_code
    )

