# GenNet Developer Guide

## Overview

This guide helps developers get started with the GenNet platform, understand the architecture, and contribute effectively.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git
- IDE (VS Code, PyCharm, etc.)

### Development Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/gennet.git
   cd gennet
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

3. **Set up Node.js environment**
   ```bash
   cd frontend/web
   npm install
   ```

4. **Start local services**
   ```bash
   make dev-up
   # Or
   ./scripts/deploy.sh local
   ```

5. **Run tests**
   ```bash
   make test
   # Or
   ./scripts/run_tests.sh
   ```

## Project Structure

```
gennet/
├── services/              # Microservices
│   ├── auth-service/
│   ├── grn-service/
│   ├── qualitative-service/
│   └── ...
├── shared/               # Shared libraries
│   ├── circuit_breaker.py
│   ├── retry.py
│   ├── cache.py
│   └── ...
├── frontend/             # Frontend application
│   └── web/
├── infrastructure/       # Infrastructure as code
│   ├── terraform/
│   └── kubernetes/
├── docs/                 # Documentation
├── scripts/              # Automation scripts
└── tests/               # Integration/E2E tests
```

## Architecture

### Microservices

Each service follows a consistent structure:

```
service-name/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── database.py          # Database configuration
├── dependencies.py      # FastAPI dependencies
├── tests/               # Service tests
├── requirements.txt     # Python dependencies
└── Dockerfile           # Container definition
```

### Shared Libraries

Shared libraries in `shared/` provide common functionality:

- **circuit_breaker.py**: Circuit breaker pattern for resilience
- **retry.py**: Retry logic with multiple strategies
- **cache.py**: Multi-layer caching
- **tracing.py**: Distributed tracing
- **apm.py**: Application performance monitoring
- **logging_middleware.py**: Structured logging

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow coding standards (Black, Flake8)
- Add type hints
- Write tests
- Update documentation

### 3. Run Tests Locally

```bash
# Unit tests
pytest services/your-service/tests/

# Integration tests
pytest tests/integration/

# All tests
make test
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `chore:` Maintenance

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Create a pull request with:
- Description of changes
- Related issues
- Test results
- Screenshots (if UI changes)

## Coding Standards

### Python

- **Style**: Black (line length 120)
- **Linting**: Flake8
- **Type Checking**: MyPy
- **Format**: 
  ```bash
  black services/
  flake8 services/
  mypy services/
  ```

### TypeScript/JavaScript

- **Style**: ESLint + Prettier
- **Type Safety**: TypeScript strict mode
- **Format**:
  ```bash
  npm run lint
  npm run format
  ```

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Type hints added where appropriate
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Error handling implemented
- [ ] Logging added for important operations

## Testing

### Unit Tests

```python
# services/your-service/tests/test_feature.py
import pytest
from your_service.feature import your_function

def test_your_function():
    result = your_function(input)
    assert result == expected
```

### Integration Tests

```python
# tests/integration/test_service_integration.py
from fastapi.testclient import TestClient
from services.your_service.main import app

client = TestClient(app)

def test_endpoint():
    response = client.get("/api/v1/endpoint")
    assert response.status_code == 200
```

### Running Tests

```bash
# All tests
pytest

# Specific service
pytest services/auth-service/tests/

# With coverage
pytest --cov=services/auth-service --cov-report=html
```

## API Development

### Creating a New Endpoint

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class RequestModel(BaseModel):
    field1: str
    field2: Optional[int] = None

@app.post("/api/v1/endpoint")
async def create_item(
    item: RequestModel,
    db: Session = Depends(get_db)
):
    """Create a new item"""
    try:
        # Implementation
        return {"id": item_id, "status": "created"}
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Error Handling

Use shared error handlers:

```python
from shared.exceptions import ValidationError, NotFoundError

try:
    # Operation
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except NotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
```

## Database Operations

### Using SQLAlchemy

```python
from database import get_db, Session
from models import YourModel

def get_item(item_id: str, db: Session = Depends(get_db)):
    item = db.query(YourModel).filter(YourModel.id == item_id).first()
    if not item:
        raise NotFoundError(f"Item {item_id} not found")
    return item
```

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## Using Shared Libraries

### Circuit Breaker

```python
from shared.circuit_breaker import circuit_breaker, CircuitBreakerConfig

@circuit_breaker("database", CircuitBreakerConfig(failure_threshold=5))
def query_database():
    # Database query
    pass
```

### Retry Logic

```python
from shared.retry import retry, STANDARD_RETRY

@retry(STANDARD_RETRY)
def unreliable_operation():
    # Operation that may fail
    pass
```

### Caching

```python
from shared.cache import cached

@cached(ttl=3600, key_func=lambda network_id: f"network:{network_id}")
def get_network(network_id: str):
    # Expensive operation
    pass
```

## Debugging

### Local Debugging

1. **Python Debugger**
   ```python
   import pdb; pdb.set_trace()
   ```

2. **VS Code Debugging**
   - Create `.vscode/launch.json`
   - Set breakpoints
   - Run debugger

3. **Logging**
   ```python
   from shared.logging_middleware import get_logger
   
   logger = get_logger(__name__)
   logger.info("Debug message")
   ```

### Docker Debugging

```bash
# View logs
docker-compose logs -f service-name

# Execute in container
docker-compose exec service-name bash

# Inspect container
docker inspect container-name
```

## Performance Optimization

### Database Queries

- Use indexes
- Avoid N+1 queries
- Use connection pooling
- Cache frequently accessed data

### Caching

- Cache expensive computations
- Use appropriate TTL values
- Invalidate cache on updates

### Async Operations

- Use async/await for I/O operations
- Use background tasks for long-running operations

## Security Best Practices

1. **Input Validation**
   - Always validate and sanitize inputs
   - Use Pydantic models
   - Check for SQL injection risks

2. **Authentication**
   - Use JWT tokens
   - Validate tokens on every request
   - Implement proper session management

3. **Secrets**
   - Never commit secrets
   - Use environment variables or secrets manager
   - Rotate secrets regularly

4. **Dependencies**
   - Keep dependencies updated
   - Check for security vulnerabilities
   - Use dependency scanning tools

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Check PYTHONPATH
   - Verify virtual environment activated
   - Check service dependencies

2. **Database Connection Issues**
   - Verify database is running
   - Check connection string
   - Verify network connectivity

3. **Service Not Starting**
   - Check logs: `docker-compose logs service-name`
   - Verify environment variables
   - Check port conflicts

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: Create GitHub issue
- **Questions**: Ask in team chat
- **Code Review**: Request review from team members

---

**Last Updated**: 2025-12-16

