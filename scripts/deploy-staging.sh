#!/bin/bash
# Staging Deployment Script
# Deploys GenNet to staging environment with validation

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

ENVIRONMENT="staging"
BASE_URL="${STAGING_BASE_URL:-https://staging-api.gennet.example.com}"

log_info "Starting staging deployment..."
echo ""

# Pre-deployment checks
log_info "Running pre-deployment checks..."
if [ -f "scripts/pre-deployment-check.sh" ]; then
    ./scripts/pre-deployment-check.sh "$ENVIRONMENT" || {
        log_error "Pre-deployment checks failed"
        exit 1
    }
else
    log_warning "Pre-deployment check script not found"
fi

# Validate dependencies
log_info "Validating dependencies..."
if [ -f "scripts/validate_dependencies.sh" ]; then
    ./scripts/validate_dependencies.sh || {
        log_error "Dependency validation failed"
        exit 1
    }
else
    log_warning "Dependency validation script not found"
fi

# Run tests
log_info "Running test suite..."
if [ -f "scripts/run_tests.sh" ]; then
    ./scripts/run_tests.sh || {
        log_error "Tests failed"
        exit 1
    }
else
    log_warning "Test script not found"
fi

# Security scan
log_info "Running security scan..."
if [ -f "scripts/security-scan.sh" ]; then
    ./scripts/security-scan.sh || {
        log_warning "Security scan found issues (review before production)"
    }
else
    log_warning "Security scan script not found"
fi

# Deploy infrastructure (if needed)
log_info "Deploying infrastructure..."
if [ -d "infrastructure/terraform" ] && [ -f "infrastructure/terraform/terraform.tfvars.staging" ]; then
    cd infrastructure/terraform
    terraform workspace select staging || terraform workspace new staging
    terraform init
    terraform plan -var-file=terraform.tfvars.staging -out=tfplan
    terraform apply tfplan
    cd ../..
else
    log_warning "Terraform staging configuration not found. Skipping infrastructure deployment."
fi

# Deploy to Kubernetes
log_info "Deploying to Kubernetes (staging)..."
if [ -d "infrastructure/kubernetes" ] && command -v kubectl &> /dev/null; then
    # Set context to staging
    kubectl config use-context staging 2>/dev/null || log_warning "Staging context not found, using current context"
    
    # Create namespace if needed
    kubectl create namespace gennet-staging --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    log_info "Applying Kubernetes manifests..."
    find infrastructure/kubernetes -name "*.yaml" -type f | while read -r file; do
        # Replace namespace if needed
        sed "s/gennet-system/gennet-staging/g" "$file" | kubectl apply -f - || log_warning "Failed to apply $file"
    done
    
    # Wait for deployments
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment --all -n gennet-staging || {
        log_warning "Some deployments may not be ready"
    }
    
    log_success "Kubernetes deployment complete!"
else
    log_warning "Kubernetes directory not found or kubectl not available"
fi

# Verify monitoring
log_info "Verifying monitoring setup..."
if [ -f "scripts/verify-monitoring.sh" ]; then
    ./scripts/verify-monitoring.sh "$ENVIRONMENT" || {
        log_warning "Monitoring verification found issues"
    }
else
    log_warning "Monitoring verification script not found"
fi

# Post-deployment validation
log_info "Running post-deployment validation..."
if [ -f "scripts/run_smoke_tests.sh" ]; then
    STAGING_BASE_URL="$BASE_URL" ./scripts/run_smoke_tests.sh "$ENVIRONMENT" "$BASE_URL" || {
        log_error "Smoke tests failed"
        exit 1
    }
else
    log_warning "Smoke test script not found"
fi

# Health check
log_info "Performing health checks..."
sleep 10  # Wait for services to stabilize

SERVICES=(
    "auth-service"
    "grn-service"
    "workflow-service"
    "qualitative-service"
    "hybrid-service"
    "ml-service"
    "health-service"
)

FAILURES=0
for service in "${SERVICES[@]}"; do
    if kubectl get deployment "$service" -n gennet-staging &> /dev/null; then
        READY=$(kubectl get deployment "$service" -n gennet-staging -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        DESIRED=$(kubectl get deployment "$service" -n gennet-staging -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
        
        if [ "$READY" = "$DESIRED" ] && [ "$READY" != "0" ]; then
            log_success "$service: $READY/$DESIRED replicas ready"
        else
            log_error "$service: $READY/$DESIRED replicas ready (expected $DESIRED)"
            ((FAILURES++))
        fi
    fi
done

# Summary
echo ""
log_info "=========================================="
log_info "Staging Deployment Summary"
log_info "=========================================="
log_info "Environment: $ENVIRONMENT"
log_info "Base URL: $BASE_URL"
log_info "Service failures: $FAILURES"
echo ""

if [ $FAILURES -eq 0 ]; then
    log_success "Staging deployment completed successfully!"
    log_info "Next steps:"
    log_info "1. Run full test suite in staging"
    log_info "2. Perform load testing"
    log_info "3. Validate all integrations"
    log_info "4. Review monitoring and alerts"
    log_info "5. Proceed to production deployment when ready"
    exit 0
else
    log_error "Staging deployment completed with $FAILURES service failure(s)"
    log_info "Review service status and logs before proceeding"
    exit 1
fi

