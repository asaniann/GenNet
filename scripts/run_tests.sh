#!/bin/bash
# Test runner script

set -e

echo "Starting test suite..."

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Not in a virtual environment"
fi

# Run linting
echo "Running linters..."
black --check services/ libraries/ || exit 1
flake8 services/ libraries/ || exit 1
isort --check-only services/ libraries/ || exit 1

# Run unit tests
echo "Running unit tests..."
pytest -m unit --cov=services --cov=libraries --cov-report=term-missing -v || exit 1

# Run integration tests (requires services to be running)
if [ "$RUN_INTEGRATION" = "true" ]; then
    echo "Running integration tests..."
    pytest -m integration --cov=services --cov-report=term-missing -v || exit 1
fi

# Run e2e tests (requires full stack)
if [ "$RUN_E2E" = "true" ]; then
    echo "Running e2e tests..."
    pytest -m e2e -v || exit 1
fi

echo "All tests passed!"

