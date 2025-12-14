.PHONY: help install dev-up dev-down test clean

help:
	@echo "GenNet Cloud Platform - Development Commands"
	@echo ""
	@echo "  make install    - Install all dependencies"
	@echo "  make dev-up     - Start development environment (Docker Compose)"
	@echo "  make dev-down   - Stop development environment"
	@echo "  make test       - Run all tests"
	@echo "  make clean      - Clean temporary files"

install:
	@echo "Installing dependencies..."
	@cd services && find . -name "requirements.txt" -exec pip install -r {} \;
	@cd frontend/web && npm install
	@cd libraries/python-sdk && pip install -e .

dev-up:
	@echo "Starting infrastructure services..."
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Infrastructure services are running!"
	@echo ""
	@echo "To start application services, run:"
	@echo "  docker-compose -f docker-compose.yml -f docker-compose.services.yml up -d"

dev-up-full:
	@echo "Starting all services (infrastructure + applications)..."
	docker-compose -f docker-compose.yml -f docker-compose.services.yml up -d
	@echo "Waiting for services to be ready..."
	@sleep 15
	@echo "All services are running!"

dev-down-full:
	docker-compose -f docker-compose.yml -f docker-compose.services.yml down -v

dev-down:
	docker-compose down

test:
	@echo "Running tests..."
	@cd services && pytest
	@cd frontend/web && npm test

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf dist/ build/ .pytest_cache/ .coverage htmlcov/

