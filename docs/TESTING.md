# Testing Guide

## Test Structure

The GenNet platform includes comprehensive test coverage across all components:

### Test Types

1. **Unit Tests** (`@pytest.mark.unit`)
   - Test individual functions and classes in isolation
   - Fast execution, no external dependencies
   - Located in `services/*/tests/test_*.py`

2. **Integration Tests** (`@pytest.mark.integration`)
   - Test service interactions and API endpoints
   - May require test databases/services
   - Located in `services/*/tests/test_*_api.py`

3. **End-to-End Tests** (`@pytest.mark.e2e`)
   - Test full workflows across services
   - Require full stack running
   - Located in `tests/integration/`

## Running Tests

### All Tests
```bash
make test
```

### Unit Tests Only
```bash
make test-unit
```

### Integration Tests Only
```bash
make test-integration
```

### E2E Tests
```bash
make test-e2e
```

### With Coverage
```bash
make test-coverage
```

### Specific Service
```bash
pytest services/auth-service/tests/
```

### Specific Test File
```bash
pytest services/auth-service/tests/test_auth.py
```

## Test Requirements

### For Unit Tests
- No external services required
- Use mocks for external dependencies

### For Integration Tests
- Requires test databases (PostgreSQL, Neo4j, Redis)
- Use Docker Compose for local testing:
  ```bash
  docker-compose up -d
  ```

### For E2E Tests
- Requires full stack running
- Set environment variables for service URLs
- Tests actual API endpoints

## Writing Tests

### Example Unit Test
```python
@pytest.mark.unit
def test_password_hashing():
    password = "testpassword"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
```

### Example Integration Test
```python
@pytest.mark.integration
def test_create_network(client, auth_token):
    response = client.post(
        "/networks",
        json={"name": "Test", "nodes": [], "edges": []},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
```

### Example E2E Test
```python
@pytest.mark.e2e
def test_workflow_e2e():
    # Register user
    # Create network
    # Run workflow
    # Check results
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `client`: FastAPI test client
- `db`: Test database session
- `auth_token`: Authentication token
- `test_user`: Sample user

## Frontend Tests

Frontend uses Jest and React Testing Library:

```bash
cd frontend/web
npm test
```

## Continuous Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- See `.github/workflows/ci.yml`

## Coverage Goals

- Unit tests: >80% coverage
- Integration tests: >60% coverage
- Critical paths: >90% coverage

