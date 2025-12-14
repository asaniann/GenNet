"""
Helper script to add Prometheus metrics to a service
"""
import sys
import re

def add_metrics_to_service(service_path: str):
    """Add metrics middleware and endpoint to a service"""
    with open(service_path, 'r') as f:
        content = f.read()
    
    # Check if already has metrics
    if 'PrometheusMiddleware' in content:
        print(f"Service {service_path} already has metrics")
        return
    
    # Add metrics import
    metrics_import = 'from shared.metrics import PrometheusMiddleware, get_metrics_response\n'
    
    # Find where to add middleware (after CorrelationIDMiddleware import)
    if 'from shared.logging_middleware import' in content:
        # Add metrics import after logging import
        logging_import_pos = content.find('from shared.logging_middleware import')
        next_line = content.find('\n', logging_import_pos)
        content = content[:next_line+1] + metrics_import + content[next_line+1:]
    else:
        # Add before app definition
        app_match = re.search(r'^app = FastAPI\(', content, re.MULTILINE)
        if app_match:
            content = content[:app_match.start()] + metrics_import + content[app_match.start():]
    
    # Add middleware before CorrelationIDMiddleware
    if 'app.add_middleware(CorrelationIDMiddleware)' in content:
        content = content.replace(
            'app.add_middleware(CorrelationIDMiddleware)',
            '# Add middleware (order matters: metrics first, then correlation ID)\napp.add_middleware(PrometheusMiddleware)\napp.add_middleware(CorrelationIDMiddleware)'
        )
    
    # Add metrics endpoint before health endpoint
    if '@app.get("/health")' in content and '@app.get("/metrics")' not in content:
        content = content.replace(
            '@app.get("/health")',
            '@app.get("/metrics")\nasync def metrics():\n    """Prometheus metrics endpoint"""\n    return get_metrics_response()\n\n\n@app.get("/health")'
        )
    
    with open(service_path, 'w') as f:
        f.write(content)
    
    print(f"Added metrics to {service_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python shared/add_metrics.py <service-main.py>")
        sys.exit(1)
    
    add_metrics_to_service(sys.argv[1])

