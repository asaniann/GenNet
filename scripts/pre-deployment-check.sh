#!/bin/bash
# Pre-Deployment Validation Script
# Validates all requirements before production deployment

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

ENVIRONMENT="${1:-production}"
ERRORS=0
WARNINGS=0

log_info "Running pre-deployment checks for: $ENVIRONMENT"
echo ""

# Check prerequisites
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 not found"
        ((ERRORS++))
        return 1
    else
        log_success "$1 found"
        return 0
    fi
}

# Check AWS CLI
log_info "Checking AWS CLI..."
if check_command aws; then
    if aws sts get-caller-identity &> /dev/null; then
        log_success "AWS credentials configured"
    else
        log_error "AWS credentials not configured"
        ((ERRORS++))
    fi
fi

# Check kubectl
log_info "Checking kubectl..."
if check_command kubectl; then
    if kubectl cluster-info &> /dev/null 2>&1; then
        log_success "Kubernetes cluster accessible"
    else
        log_warning "Kubernetes cluster not accessible (may need to configure)"
        ((WARNINGS++))
    fi
fi

# Check Terraform
log_info "Checking Terraform..."
if check_command terraform; then
    TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version' 2>/dev/null || echo "unknown")
    log_info "Terraform version: $TERRAFORM_VERSION"
fi

# Check Docker
log_info "Checking Docker..."
if check_command docker; then
    if docker ps &> /dev/null; then
        log_success "Docker daemon running"
    else
        log_warning "Docker daemon not running"
        ((WARNINGS++))
    fi
fi

# Check Terraform configuration
log_info "Checking Terraform configuration..."
if [ -f "infrastructure/terraform/terraform.tfvars" ]; then
    log_success "terraform.tfvars found"
    
    # Check for required variables
    REQUIRED_VARS=("project_name" "environment" "aws_region")
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}" infrastructure/terraform/terraform.tfvars; then
            log_success "Required variable $var found"
        else
            log_warning "Required variable $var not found in terraform.tfvars"
            ((WARNINGS++))
        fi
    done
else
    log_error "terraform.tfvars not found"
    ((ERRORS++))
fi

# Check Kubernetes configuration
log_info "Checking Kubernetes configuration..."
if kubectl get namespace gennet-system &> /dev/null 2>&1; then
    log_success "gennet-system namespace exists"
else
    log_warning "gennet-system namespace does not exist (will be created)"
    ((WARNINGS++))
fi

# Check secrets
log_info "Checking secrets configuration..."
if [ -d "infrastructure/kubernetes/external-secrets" ]; then
    log_success "External secrets configuration found"
else
    log_warning "External secrets configuration not found"
    ((WARNINGS++))
fi

# Check Docker images
log_info "Checking Docker images..."
if [ -n "${DOCKER_REGISTRY:-}" ]; then
    log_success "Docker registry configured: $DOCKER_REGISTRY"
else
    log_warning "DOCKER_REGISTRY not set (using local images)"
    ((WARNINGS++))
fi

# Check test coverage
log_info "Checking test coverage..."
if [ -f "coverage.xml" ] || [ -f "coverage.json" ]; then
    log_success "Test coverage report found"
else
    log_warning "Test coverage report not found (run tests first)"
    ((WARNINGS++))
fi

# Check documentation
log_info "Checking documentation..."
REQUIRED_DOCS=(
    "docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md"
    "docs/RUNBOOKS.md"
    "docs/API_DOCUMENTATION.md"
    "docs/COMPLIANCE.md"
)

for doc in "${REQUIRED_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        log_success "Documentation found: $doc"
    else
        log_warning "Documentation missing: $doc"
        ((WARNINGS++))
    fi
done

# Summary
echo ""
log_info "=========================================="
log_info "Pre-Deployment Check Summary"
log_info "=========================================="
log_info "Errors: $ERRORS"
log_info "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        log_success "All checks passed! Ready for deployment."
        exit 0
    else
        log_warning "Checks passed with warnings. Review warnings before deployment."
        exit 0
    fi
else
    log_error "Checks failed with $ERRORS error(s). Fix errors before deployment."
    exit 1
fi

