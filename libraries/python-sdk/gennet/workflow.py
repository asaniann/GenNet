"""Workflow model"""

from typing import Dict, Any, Optional
from enum import Enum


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Workflow:
    """Represents an analysis workflow"""
    
    def __init__(self, data: Dict[str, Any], client=None):
        self.id = data['id']
        self.name = data['name']
        self.workflow_type = data['workflow_type']
        self.network_id = data['network_id']
        self.status = WorkflowStatus(data['status'])
        self.progress = data.get('progress', 0)
        self.results = data.get('results')
        self._client = client
    
    def __repr__(self):
        return f"<Workflow id={self.id} type={self.workflow_type} status={self.status.value}>"
    
    def wait_for_completion(self, timeout: Optional[int] = None):
        """Wait for workflow to complete"""
        if not self._client:
            raise ValueError("Client not set")
        
        import time
        start_time = time.time()
        
        while self.status not in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError("Workflow did not complete within timeout")
            
            status_data = self._client.get_workflow_status(self.id)
            self.status = WorkflowStatus(status_data['status'])
            self.progress = status_data.get('progress', 0)
            
            time.sleep(2)

