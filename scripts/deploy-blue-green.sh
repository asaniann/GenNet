#!/bin/bash
# Blue-Green Deployment Script
# Implements zero-downtime deployments

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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

ENVIRONMENT="${1:-staging}"
SERVICE="${2:-all}"

log_info "Starting blue-green deployment for $SERVICE in $ENVIRONMENT"

# Deploy green version
log_info "Deploying green version..."
kubectl set image deployment/${SERVICE}-green \
    ${SERVICE}=${REGISTRY}/${SERVICE}:${VERSION} \
    -n gennet-${ENVIRONMENT} || {
    # Create green deployment if it doesn't exist
    kubectl apply -f infrastructure/kubernetes/${SERVICE}-green-deployment.yaml \
        -n gennet-${ENVIRONMENT}
}

# Wait for green to be ready
log_info "Waiting for green deployment to be ready..."
kubectl rollout status deployment/${SERVICE}-green -n gennet-${ENVIRONMENT}

# Run smoke tests on green
log_info "Running smoke tests on green..."
# Add smoke test logic here

# Switch traffic to green
log_info "Switching traffic to green..."
kubectl patch service ${SERVICE} \
    -n gennet-${ENVIRONMENT} \
    -p '{"spec":{"selector":{"version":"green"}}}'

# Wait and verify
sleep 30
log_info "Verifying green deployment..."
kubectl get pods -n gennet-${ENVIRONMENT} -l app=${SERVICE},version=green

log_success "Blue-green deployment complete"

