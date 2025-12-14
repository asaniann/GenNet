"""
Helper script to add logging to a service
Usage: python shared/add_logging.py services/service-name/main.py
"""
import sys
import re

def add_logging_to_service(service_path: str):
    """Add logging imports and middleware to a service file"""
    with open(service_path, 'r') as f:
        content = f.read()
    
    # Check if already has logging
    if 'CorrelationIDMiddleware' in content:
        print(f"Service {service_path} already has logging middleware")
        return
    
    # Add imports after existing imports
    logging_import = '''import logging
import sys
import os

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import correlation ID middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.logging_middleware import CorrelationIDMiddleware, get_logger

'''
    
    # Find where to insert (after last import, before app definition)
    app_match = re.search(r'^app = FastAPI\(', content, re.MULTILINE)
    if app_match:
        insert_pos = app_match.start()
        # Find last import before app
        import_pattern = r'^from .+ import .+$|^import .+$'
        imports = list(re.finditer(import_pattern, content[:insert_pos], re.MULTILINE))
        if imports:
            last_import = imports[-1]
            insert_pos = last_import.end() + 1
        
        content = content[:insert_pos] + '\n' + logging_import + content[insert_pos:]
    else:
        # Add at the beginning if FastAPI not found
        content = logging_import + content
    
    # Add middleware after app definition
    if 'app.add_middleware(CorrelationIDMiddleware)' not in content:
        app_def_match = re.search(r'^app = FastAPI\([^)]+\)', content, re.MULTILINE | re.DOTALL)
        if app_def_match:
            insert_pos = app_def_match.end()
            middleware_add = '\n\n# Add correlation ID middleware\napp.add_middleware(CorrelationIDMiddleware)\n\nlogger = get_logger(__name__)\n'
            content = content[:insert_pos] + middleware_add + content[insert_pos:]
    
    # Add logger to startup event
    startup_pattern = r'@app\.on_event\("startup"\)\s+async def startup_event\(\):'
    if re.search(startup_pattern, content):
        content = re.sub(
            r'(async def startup_event\(\):\s+)("""Initialize.*?"""\s+)',
            r'\1logger.info("Starting service...")\n    \2',
            content
        )
    
    with open(service_path, 'w') as f:
        f.write(content)
    
    print(f"Added logging to {service_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python shared/add_logging.py <service-main.py>")
        sys.exit(1)
    
    add_logging_to_service(sys.argv[1])

