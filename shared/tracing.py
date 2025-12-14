"""
Distributed tracing with OpenTelemetry
"""
import os
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry
OTEL_AVAILABLE = False
tracer = None
Span = None

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    OTEL_AVAILABLE = True
    Span = trace.Span
except ImportError:
    logger.warning("OpenTelemetry not available. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi")
    # Create mock classes for when OTEL is not available
    class MockSpan:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def set_attribute(self, *args): pass
        def add_event(self, *args): pass
        def set_status(self, *args): pass
    
    Span = MockSpan


def init_tracing(
    service_name: str,
    service_version: str = "1.0.0",
    endpoint: Optional[str] = None,
    enabled: bool = True
):
    """
    Initialize OpenTelemetry tracing
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        endpoint: OTLP endpoint (defaults to OTEL_EXPORTER_OTLP_ENDPOINT env var)
        enabled: Whether tracing is enabled
    """
    global tracer, OTEL_AVAILABLE
    
    if not enabled or not OTEL_AVAILABLE:
        logger.info("Tracing disabled or OpenTelemetry not available")
        return None
    
    try:
        # Get endpoint from env or parameter
        endpoint = endpoint or os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')
        
        # Create resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer(service_name, service_version)
        
        logger.info(f"OpenTelemetry tracing initialized for {service_name}")
        return tracer
    
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        OTEL_AVAILABLE = False
        return None


def get_tracer():
    """Get the global tracer instance"""
    global tracer
    if tracer is None:
        if OTEL_AVAILABLE:
            tracer = trace.get_tracer(__name__)
        else:
            return None
    return tracer


def trace_function(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace a function
    
    Usage:
        @trace_function(name="process_workflow", attributes={"workflow.type": "qualitative"})
        async def process_workflow(workflow_id: str):
            # Function implementation
            pass
    """
    def decorator(func):
        span_name = name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_tracer = get_tracer()
            if current_tracer:
                with current_tracer.start_as_current_span(span_name) as span:
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, str(value))
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(trace.Status(trace.StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            else:
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_tracer = get_tracer()
            if current_tracer:
                with current_tracer.start_as_current_span(span_name) as span:
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, str(value))
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(trace.Status(trace.StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            else:
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def instrument_fastapi(app):
    """
    Instrument FastAPI application with OpenTelemetry
    
    Args:
        app: FastAPI application instance
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, skipping FastAPI instrumentation")
        return
    
    try:
        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


def instrument_sqlalchemy(engine):
    """
    Instrument SQLAlchemy engine with OpenTelemetry
    
    Args:
        engine: SQLAlchemy engine instance
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, skipping SQLAlchemy instrumentation")
        return
    
    try:
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument SQLAlchemy: {e}")

