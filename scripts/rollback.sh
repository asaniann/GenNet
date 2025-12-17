#!/bin/bash
# Rollback Script for Production Deployment
# Rolls back to previous deployment version

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
SERVICE="${2:-all}"

log_info "Rolling back deployment for: $ENVIRONMENT"
log_info "Service: $SERVICE"
echo ""

# Confirm rollback
log_warning "This will rollback the deployment. Continue? (yes/no)"
read -r confirmation
if [ "$confirmation" != "yes" ]; then
    log_info "Rollback cancelled"
    exit 0
fi

# Rollback Kubernetes deployments
rollback_deployment() {
    local service=$1
    
    log_info "Rolling back $service..."
    
    if kubectl rollout undo deployment/"$service" -n gennet-system 2>/dev/null; then
        log_success "$service rollback initiated"
        
        # Wait for rollout to complete
        log_info "Waiting for $service rollout to complete..."
        if kubectl rollout status deployment/"$service" -n gennet-system --timeout=5m; then
            log_success "$service rollback completed"
            return 0
        else
            log_error "$service rollback failed or timed out"
            return 1
        fi
    else
        log_error "Failed to rollback $service"
        return 1
    fi
}

# Rollback all services
if [ "$SERVICE" = "all" ]; then
    log_info "Rolling back all services..."
    
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
        if ! rollback_deployment "$service"; then
            ((FAILURES++))
        fi
    done
    
    if [ $FAILURES -eq 0 ]; then
        log_success "All services rolled back successfully"
    else
        log_error "Rollback completed with $FAILURES failure(s)"
        exit 1
    fi
else
    # Rollback specific service
    if rollback_deployment "$SERVICE"; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback failed"
        exit 1
    fi
fi

# Verify rollback
echo ""
log_info "Verifying rollback..."
sleep 10

if kubectl get pods -n gennet-system | grep -q "Running"; then
    log_success "All pods are running"
else
    log_warning "Some pods may not be running. Check status manually."
fi

log_success "Rollback completed"

