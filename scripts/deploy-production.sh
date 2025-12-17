#!/bin/bash
# Production Deployment Script
# Deploys GenNet to production with full validation and monitoring

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

ENVIRONMENT="production"
BASE_URL="${PRODUCTION_BASE_URL:-https://api.gennet.example.com}"

log_info "Starting PRODUCTION deployment..."
log_warning "This will deploy to PRODUCTION. Are you sure? (yes/no)"
read -r confirmation
if [ "$confirmation" != "yes" ]; then
    log_info "Deployment cancelled"
    exit 0
fi

echo ""

# Pre-deployment checks
log_info "Running pre-deployment checks..."
if [ -f "scripts/pre-deployment-check.sh" ]; then
    ./scripts/pre-deployment-check.sh "$ENVIRONMENT" || {
        log_error "Pre-deployment checks failed"
        exit 1
    }
else
    log_error "Pre-deployment check script not found"
    exit 1
fi

# Validate dependencies
log_info "Validating dependencies..."
if [ -f "scripts/validate_dependencies.sh" ]; then
    ./scripts/validate_dependencies.sh || {
        log_error "Dependency validation failed"
        exit 1
    }
else
    log_error "Dependency validation script not found"
    exit 1
fi

# Security scan (must pass for production)
log_info "Running security scan (required for production)..."
if [ -f "scripts/security-scan.sh" ]; then
    ./scripts/security-scan.sh || {
        log_error "Security scan failed. Fix issues before deploying to production."
        exit 1
    }
else
    log_error "Security scan script not found"
    exit 1
fi

# Verify staging deployment
log_warning "Have you successfully deployed and tested in staging? (yes/no)"
read -r staging_confirmed
if [ "$staging_confirmed" != "yes" ]; then
    log_error "Staging deployment must be successful before production deployment"
    exit 1
fi

# Review production checklist
log_info "Review production deployment checklist..."
if [ -f "docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md" ]; then
    log_warning "Please review docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md"
    log_warning "Have all checklist items been completed? (yes/no)"
    read -r checklist_confirmed
    if [ "$checklist_confirmed" != "yes" ]; then
        log_error "All checklist items must be completed before production deployment"
        exit 1
    fi
else
    log_error "Production deployment checklist not found"
    exit 1
fi

# Deploy infrastructure
log_info "Deploying infrastructure..."
if [ -d "infrastructure/terraform" ] && [ -f "infrastructure/terraform/terraform.tfvars" ]; then
    cd infrastructure/terraform
    
    # Use production workspace
    terraform workspace select production || terraform workspace new production
    
    # Initialize
    terraform init || {
        log_error "Terraform initialization failed"
        exit 1
    }
    
    # Plan
    log_info "Creating Terraform plan..."
    terraform plan -var-file=terraform.tfvars -out=tfplan || {
        log_error "Terraform plan failed"
        exit 1
    }
    
    # Review plan
    log_warning "Review Terraform plan above. Continue with apply? (yes/no)"
    read -r apply_confirmed
    if [ "$apply_confirmed" != "yes" ]; then
        log_info "Terraform apply cancelled"
        exit 0
    fi
    
    # Apply
    log_info "Applying Terraform configuration..."
    terraform apply tfplan || {
        log_error "Terraform apply failed"
        exit 1
    }
    
    cd ../..
else
    log_error "Terraform configuration not found"
    exit 1
fi

# Deploy to Kubernetes
log_info "Deploying to Kubernetes (production)..."
if [ -d "infrastructure/kubernetes" ] && command -v kubectl &> /dev/null; then
    # Verify production context
    CURRENT_CONTEXT=$(kubectl config current-context)
    log_info "Current Kubernetes context: $CURRENT_CONTEXT"
    log_warning "Is this the correct production context? (yes/no)"
    read -r context_confirmed
    if [ "$context_confirmed" != "yes" ]; then
        log_error "Please switch to the correct production context"
        exit 1
    fi
    
    # Create namespace
    kubectl create namespace gennet-system --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    log_info "Applying Kubernetes manifests..."
    find infrastructure/kubernetes -name "*.yaml" -type f | while read -r file; do
        kubectl apply -f "$file" || {
            log_error "Failed to apply $file"
            exit 1
        }
    done
    
    # Wait for deployments
    log_info "Waiting for deployments to be ready (this may take several minutes)..."
    kubectl wait --for=condition=available --timeout=600s deployment --all -n gennet-system || {
        log_error "Deployments not ready within timeout"
        exit 1
    }
    
    log_success "Kubernetes deployment complete!"
else
    log_error "Kubernetes directory not found or kubectl not available"
    exit 1
fi

# Verify monitoring
log_info "Verifying monitoring setup..."
if [ -f "scripts/verify-monitoring.sh" ]; then
    ./scripts/verify-monitoring.sh "$ENVIRONMENT" || {
        log_error "Monitoring verification failed"
        exit 1
    }
else
    log_error "Monitoring verification script not found"
    exit 1
fi

# Post-deployment validation
log_info "Running post-deployment smoke tests..."
if [ -f "scripts/run_smoke_tests.sh" ]; then
    PRODUCTION_BASE_URL="$BASE_URL" ./scripts/run_smoke_tests.sh "$ENVIRONMENT" "$BASE_URL" || {
        log_error "Smoke tests failed"
        log_info "Consider rolling back if critical issues detected"
        exit 1
    }
else
    log_error "Smoke test script not found"
    exit 1
fi

# Health check
log_info "Performing health checks..."
sleep 15  # Wait for services to stabilize

SERVICES=(
    "auth-service"
    "grn-service"
    "workflow-service"
    "qualitative-service"
    "hybrid-service"
    "ml-service"
    "health-service"
    "api-gateway"
)

FAILURES=0
for service in "${SERVICES[@]}"; do
    if kubectl get deployment "$service" -n gennet-system &> /dev/null; then
        READY=$(kubectl get deployment "$service" -n gennet-system -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        DESIRED=$(kubectl get deployment "$service" -n gennet-system -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
        
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
log_info "Production Deployment Summary"
log_info "=========================================="
log_info "Environment: $ENVIRONMENT"
log_info "Base URL: $BASE_URL"
log_info "Service failures: $FAILURES"
echo ""

if [ $FAILURES -eq 0 ]; then
    log_success "✅ PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo ""
    log_info "Post-Deployment Tasks:"
    log_info "1. Monitor services for 24 hours"
    log_info "2. Review metrics and logs"
    log_info "3. Verify all integrations"
    log_info "4. Check alerting channels"
    log_info "5. Review user feedback"
    echo ""
    log_info "Monitoring:"
    log_info "- Prometheus: Check service metrics"
    log_info "- Grafana: Review dashboards"
    log_info "- Alerts: Verify alerting is working"
    log_info "- Logs: Monitor for errors"
    echo ""
    log_warning "Keep rollback script ready: ./scripts/rollback.sh production"
    exit 0
else
    log_error "Production deployment completed with $FAILURES service failure(s)"
    log_info "Review service status and logs immediately"
    log_info "Consider rollback: ./scripts/rollback.sh production"
    exit 1
fi

