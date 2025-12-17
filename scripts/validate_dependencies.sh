#!/bin/bash
# Dependency Validation Script
# Validates all dependencies are available and compatible

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

ERRORS=0
WARNINGS=0

log_info "Validating dependencies..."
echo ""

# Check Python version
log_info "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_PYTHON="3.11"

if [ "$(printf '%s\n' "$REQUIRED_PYTHON" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_PYTHON" ]; then
    log_success "Python $PYTHON_VERSION >= $REQUIRED_PYTHON"
else
    log_error "Python $PYTHON_VERSION < $REQUIRED_PYTHON (required)"
    ((ERRORS++))
fi

# Check Node.js version
log_info "Checking Node.js version..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d. -f1,2)
    REQUIRED_NODE="18.0"
    
    if [ "$(printf '%s\n' "$REQUIRED_NODE" "$NODE_VERSION" | sort -V | head -n1)" = "$REQUIRED_NODE" ]; then
        log_success "Node.js $NODE_VERSION >= $REQUIRED_NODE"
    else
        log_warning "Node.js $NODE_VERSION < $REQUIRED_NODE (recommended)"
        ((WARNINGS++))
    fi
else
    log_warning "Node.js not found (optional for backend-only development)"
    ((WARNINGS++))
fi

# Check Docker
log_info "Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | cut -d',' -f1)
    log_success "Docker $DOCKER_VERSION found"
    
    if docker ps &> /dev/null; then
        log_success "Docker daemon running"
    else
        log_warning "Docker daemon not running"
        ((WARNINGS++))
    fi
else
    log_error "Docker not found"
    ((ERRORS++))
fi

# Check Docker Compose
log_info "Checking Docker Compose..."
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    log_success "Docker Compose found"
else
    log_error "Docker Compose not found"
    ((ERRORS++))
fi

# Check Python packages
log_info "Checking Python packages..."
REQUIRED_PACKAGES=("fastapi" "pydantic" "sqlalchemy" "pytest")

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        log_success "Python package $package installed"
    else
        log_warning "Python package $package not installed"
        ((WARNINGS++))
    fi
done

# Check security vulnerabilities
log_info "Checking for known security vulnerabilities..."
if command -v safety &> /dev/null; then
    if safety check --json &> /dev/null; then
        log_success "No known security vulnerabilities"
    else
        log_warning "Some security vulnerabilities detected (run 'safety check' for details)"
        ((WARNINGS++))
    fi
else
    log_warning "safety not installed (install with: pip install safety)"
    ((WARNINGS++))
fi

# Summary
echo ""
log_info "=========================================="
log_info "Dependency Validation Summary"
log_info "=========================================="
log_info "Errors: $ERRORS"
log_info "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        log_success "All dependencies validated successfully!"
        exit 0
    else
        log_warning "Dependencies validated with warnings. Review warnings above."
        exit 0
    fi
else
    log_error "Dependency validation failed with $ERRORS error(s). Fix errors before proceeding."
    exit 1
fi

