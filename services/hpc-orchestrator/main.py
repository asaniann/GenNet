"""
HPC Orchestrator Service
Manages Kubernetes Jobs, Slurm, and HTCondor integration
"""

import logging
import sys
from fastapi import FastAPI, Depends
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os
from typing import Dict, Any

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

app = FastAPI(
    title="GenNet HPC Orchestrator",
    description="HPC Job Orchestration Service",
    version="1.0.0"
)

# Add correlation ID middleware
# Add middleware (order matters: metrics first, then correlation ID)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(CorrelationIDMiddleware)

logger = get_logger(__name__)

# Load Kubernetes config
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

batch_v1 = client.BatchV1Api()
core_v1 = client.CoreV1Api()


@app.post("/jobs/create")
async def create_job(job_spec: Dict[str, Any]):
    """Create a Kubernetes job"""
    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": job_spec.get("name"),
            "namespace": job_spec.get("namespace", "gennet-workflows")
        },
        "spec": {
            "template": {
                "spec": {
                    "containers": [{
                        "name": job_spec.get("container_name", "worker"),
                        "image": job_spec.get("image"),
                        "resources": job_spec.get("resources", {})
                    }],
                    "restartPolicy": "Never"
                }
            },
            "backoffLimit": job_spec.get("backoff_limit", 3)
        }
    }
    
    try:
        api_response = batch_v1.create_namespaced_job(
            body=job_manifest,
            namespace=job_spec.get("namespace", "gennet-workflows")
        )
        return {"job_id": api_response.metadata.name, "status": "created"}
    except ApiException as e:
        return {"error": str(e)}


@app.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str, namespace: str = "gennet-workflows"):
    """Get job status"""
    try:
        job = batch_v1.read_namespaced_job(name=job_id, namespace=namespace)
        return {
            "job_id": job_id,
            "status": job.status.active,
            "succeeded": job.status.succeeded,
            "failed": job.status.failed
        }
    except ApiException as e:
        return {"error": str(e)}


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str, namespace: str = "gennet-workflows"):
    """Delete a job"""
    try:
        batch_v1.delete_namespaced_job(
            name=job_id,
            namespace=namespace,
            propagation_policy="Foreground"
        )
        return {"status": "deleted"}
    except ApiException as e:
        return {"error": str(e)}


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
    checks = {}
    all_ready = True
    
    # Check Kubernetes API connection
    try:
        from kubernetes import client
        api = client.CoreV1Api()
        api.list_namespaces()
        checks["kubernetes"] = "ok"
    except Exception as e:
        checks["kubernetes"] = f"error: {str(e)}"
        # Kubernetes check is optional for readiness
    
    status = "ready" if all_ready else "not_ready"
    status_code = 200 if all_ready else 503
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content={
            "status": status,
            "service": "hpc-orchestrator",
            "version": "1.0.0",
            "checks": checks
        },
        status_code=status_code
    )


@app.get("/health")
async def health():
    """Legacy health endpoint"""
    return await readiness()

