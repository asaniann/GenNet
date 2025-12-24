# Testing Guide

## Overview

Comprehensive testing strategy for GenNet services with >90% coverage target.

## Test Structure

```
tests/
├── conftest_shared.py      # Shared fixtures
├── integration/
│   └── test_all_services.py
└── performance/
    └── test_load_all_services.py

services/*/tests/
├── __init__.py
├── conftest.py            # Service-specific fixtures
└── test_*.py              # Service tests
```

## Running Tests

### All Tests

```bash
pytest
```

### With Coverage

```bash
pytest --cov=services --cov=shared --cov-report=html
```

### Specific Test Types

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Performance tests
pytest -m performance

# Security tests
pytest -m security
```

## Test Coverage Target

- **Target**: >90% coverage for all services
- **Current**: Test infrastructure in place, tests being expanded

## Test Types

### Unit Tests

Test individual components and functions in isolation.

### Integration Tests

Test service-to-service communication and workflows.

### E2E Tests

Test complete user workflows end-to-end.

### Performance Tests

Test service performance under load.

### Security Tests

Test authentication, authorization, and input validation.

## Writing Tests

See existing test files in `services/*/tests/` for examples.

