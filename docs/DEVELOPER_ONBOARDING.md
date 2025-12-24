# Developer Onboarding Guide

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Neo4j 5+
- Redis 7+

### Setup

1. **Clone Repository**

```bash
git clone <repository-url>
cd GenNet
```

2. **Install Dependencies**

```bash
pip install -r requirements-dev.txt
```

3. **Start Infrastructure**

```bash
docker-compose up -d
```

4. **Start Services**

```bash
docker-compose -f docker-compose.yml -f docker-compose.services.yml up
```

## Development Workflow

### 1. Service Development

- Create service directory in `services/`
- Follow existing service patterns
- Add tests in `services/{service}/tests/`
- Update `docker-compose.services.yml`

### 2. Testing

```bash
# Run tests for a service
pytest services/{service}/tests/

# Run all tests
pytest

# With coverage
pytest --cov
```

### 3. Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Run linters: `pylint`, `black`, `mypy`

## Service Structure

```
services/{service}/
├── main.py              # FastAPI app
├── models.py            # Database models
├── database.py          # Database config
├── dependencies.py      # Dependencies
├── requirements.txt      # Dependencies
├── Dockerfile           # Docker config
└── tests/               # Tests
```

## Shared Utilities

- `shared/http_client.py`: Service-to-service HTTP client
- `shared/logging_middleware.py`: Structured logging
- `shared/metrics.py`: Prometheus metrics
- `shared/error_handler.py`: Error handling
- `shared/kafka_publisher.py`: Kafka event publishing

## API Documentation

Each service provides auto-generated API documentation:

- Swagger UI: `http://localhost:{port}/docs`
- ReDoc: `http://localhost:{port}/redoc`

## Common Tasks

### Adding a New Service

1. Create service directory
2. Implement models, database, main.py
3. Add Dockerfile
4. Update docker-compose.services.yml
5. Add tests
6. Update documentation

### Adding a New Endpoint

1. Add endpoint to `main.py`
2. Add Pydantic models to `models.py`
3. Add tests
4. Update API documentation

## Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Docker Documentation: https://docs.docker.com/

