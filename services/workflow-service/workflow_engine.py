"""
Workflow execution engine
"""

from models import Workflow, JobStatus
from database import SessionLocal
from datetime import datetime
import os
import sys

# Import shared HTTP client with retries and timeouts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.http_client import call_service


class WorkflowEngine:
    """Orchestrates workflow execution"""
    
    def __init__(self):
        self.qualitative_service_url = os.getenv("QUALITATIVE_SERVICE_URL", "http://qualitative-service:8000")
        self.hybrid_service_url = os.getenv("HYBRID_SERVICE_URL", "http://hybrid-service:8000")
        self.ml_service_url = os.getenv("ML_SERVICE_URL", "http://ml-service:8000")
    
    def execute_workflow(self, workflow_id: str):
        """Execute a workflow"""
        db = SessionLocal()
        try:
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not workflow:
                return
            
            workflow.status = JobStatus.RUNNING
            workflow.started_at = datetime.utcnow()
            workflow.progress = 0
            db.commit()
            
            try:
                if workflow.workflow_type == "qualitative":
                    self._execute_qualitative_workflow(workflow, db)
                elif workflow.workflow_type == "hybrid":
                    self._execute_hybrid_workflow(workflow, db)
                elif workflow.workflow_type == "ml":
                    self._execute_ml_workflow(workflow, db)
                else:
                    raise ValueError(f"Unknown workflow type: {workflow.workflow_type}")
                
                workflow.status = JobStatus.COMPLETED
                workflow.progress = 100
                workflow.completed_at = datetime.utcnow()
            
            except Exception as e:
                workflow.status = JobStatus.FAILED
                workflow.error_message = str(e)
            
            finally:
                db.commit()
        
        finally:
            db.close()
    
    def _execute_qualitative_workflow(self, workflow: Workflow, db):
        """Execute qualitative modeling workflow"""
        # Step 1: CTL verification
        workflow.progress = 20
        db.commit()
        
        # Step 2: Parameter generation
        workflow.progress = 40
        db.commit()
        
        # Step 3: Parameter filtering
        workflow.progress = 60
        db.commit()
        
        # Step 4: State graph generation
        workflow.progress = 80
        db.commit()
        
        # Store results
        workflow.results = {
            "parameters": [],
            "state_graph": {}
        }
    
    def _execute_hybrid_workflow(self, workflow: Workflow, db):
        """Execute hybrid modeling workflow"""
        # Placeholder for hybrid workflow execution
        workflow.progress = 50
        db.commit()
        
        workflow.results = {
            "time_delays": {},
            "trajectories": []
        }
    
    def _execute_ml_workflow(self, workflow: Workflow, db):
        """Execute ML workflow"""
        # Placeholder for ML workflow execution
        workflow.progress = 50
        db.commit()
        
        workflow.results = {
            "predictions": {},
            "model_metrics": {}
        }

