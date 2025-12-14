"""
Async task queue integration for background job processing
Supports both Celery and RQ (Redis Queue)
"""
import os
import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import task queue libraries
CELERY_AVAILABLE = False
RQ_AVAILABLE = False

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    pass

try:
    import redis
    from rq import Queue, Retry
    RQ_AVAILABLE = True
except ImportError:
    pass


class TaskQueueType(str, Enum):
    """Task queue type enumeration"""
    CELERY = "celery"
    RQ = "rq"
    SYNC = "sync"  # Fallback to synchronous execution


class TaskQueue:
    """
    Unified task queue interface supporting Celery and RQ
    
    Automatically selects available backend or falls back to sync execution
    """
    
    def __init__(
        self,
        queue_type: Optional[TaskQueueType] = None,
        broker_url: Optional[str] = None,
        result_backend: Optional[str] = None
    ):
        self.queue_type = queue_type
        self.broker_url = broker_url or os.getenv('REDIS_URL', 'redis://redis:6379/0')
        self.result_backend = result_backend or self.broker_url
        
        # Auto-detect queue type if not specified
        if not self.queue_type:
            if CELERY_AVAILABLE:
                self.queue_type = TaskQueueType.CELERY
            elif RQ_AVAILABLE:
                self.queue_type = TaskQueueType.RQ
            else:
                self.queue_type = TaskQueueType.SYNC
                logger.warning("No task queue backend available, using synchronous execution")
        
        # Initialize the selected backend
        if self.queue_type == TaskQueueType.CELERY and CELERY_AVAILABLE:
            self._init_celery()
        elif self.queue_type == TaskQueueType.RQ and RQ_AVAILABLE:
            self._init_rq()
        else:
            self._init_sync()
    
    def _init_celery(self):
        """Initialize Celery backend"""
        self.celery_app = Celery(
            'gennet',
            broker=self.broker_url,
            backend=self.result_backend
        )
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=30 * 60,  # 30 minutes
            task_soft_time_limit=25 * 60,  # 25 minutes
            worker_prefetch_multiplier=4,
            worker_max_tasks_per_child=1000,
        )
        logger.info("Celery task queue initialized")
    
    def _init_rq(self):
        """Initialize RQ (Redis Queue) backend"""
        try:
            import redis
            redis_conn = redis.from_url(self.broker_url)
            self.rq_queue = Queue('default', connection=redis_conn)
            self.redis_conn = redis_conn
            logger.info("RQ task queue initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RQ: {e}")
            self._init_sync()
    
    def _init_sync(self):
        """Initialize synchronous fallback"""
        logger.warning("Using synchronous task execution (no queue backend)")
        self.sync_mode = True
    
    def task(
        self,
        name: Optional[str] = None,
        queue: str = "default",
        timeout: Optional[int] = None,
        retry: bool = True,
        max_retries: int = 3,
        retry_delay: int = 60
    ):
        """
        Decorator to register a function as a task
        
        Usage:
            @task_queue.task(name="process_workflow", timeout=600)
            def process_workflow(workflow_id: str):
                # Long-running task
                pass
        """
        def decorator(func: Callable):
            task_name = name or f"{func.__module__}.{func.__name__}"
            
            if self.queue_type == TaskQueueType.CELERY:
                # Register as Celery task
                celery_task = self.celery_app.task(
                    name=task_name,
                    bind=True,
                    max_retries=max_retries,
                    default_retry_delay=retry_delay,
                    time_limit=timeout,
                    soft_time_limit=timeout * 0.9 if timeout else None
                )(func)
                return celery_task
            
            elif self.queue_type == TaskQueueType.RQ:
                # For RQ, we'll create a wrapper function
                def rq_task(*args, **kwargs):
                    job = self.rq_queue.enqueue(
                        func,
                        *args,
                        **kwargs,
                        job_timeout=timeout or 300,
                        retry=Retry(max=max_retries, interval=[retry_delay]) if retry else None
                    )
                    return job
                
                rq_task.task_name = task_name
                rq_task.is_async = True
                return rq_task
            
            else:
                # Synchronous execution
                func.is_async = False
                return func
        
        return decorator
    
    def delay(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a task asynchronously
        
        Usage:
            result = task_queue.delay(process_workflow, workflow_id="abc123")
        """
        if self.queue_type == TaskQueueType.CELERY:
            if hasattr(func, 'delay'):
                return func.delay(*args, **kwargs)
            else:
                # Function not decorated, create task on-the-fly
                return self.celery_app.send_task(func.__name__, args=args, kwargs=kwargs)
        
        elif self.queue_type == TaskQueueType.RQ:
            if hasattr(func, 'is_async') and func.is_async:
                return func(*args, **kwargs)  # Already returns job
            else:
                job = self.rq_queue.enqueue(func, *args, **kwargs)
                return job
        
        else:
            # Synchronous execution
            return func(*args, **kwargs)
    
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task result by ID
        
        Args:
            task_id: Task ID returned from delay()
        
        Returns:
            Task result or None if not ready
        """
        if self.queue_type == TaskQueueType.CELERY:
            result = self.celery_app.AsyncResult(task_id)
            if result.ready():
                return {
                    "status": result.status,
                    "result": result.result,
                    "traceback": result.traceback
                }
            return {"status": result.status}
        
        elif self.queue_type == TaskQueueType.RQ:
            from rq.job import Job
            job = Job.fetch(task_id, connection=self.redis_conn)
            return {
                "status": job.get_status(),
                "result": job.result if job.is_finished else None,
                "exception": str(job.exc_info) if job.is_failed else None
            }
        
        return None


# Global task queue instance
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """Get or create global task queue instance"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue


def task(
    name: Optional[str] = None,
    queue: str = "default",
    timeout: Optional[int] = None,
    retry: bool = True,
    max_retries: int = 3
):
    """
    Convenience decorator for task registration
    
    Usage:
        @task(name="process_workflow", timeout=600)
        def process_workflow(workflow_id: str):
            # Task implementation
            pass
    """
    return get_task_queue().task(name=name, queue=queue, timeout=timeout, retry=retry, max_retries=max_retries)

