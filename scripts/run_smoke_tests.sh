#!/bin/bash
# Smoke Tests for Production Deployment
# Quick validation tests after deployment

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

ENVIRONMENT="${1:-production}"
BASE_URL="${2:-https://api.gennet.example.com}"
FAILURES=0

log_info "Running smoke tests for: $ENVIRONMENT"
log_info "Base URL: $BASE_URL"
echo ""

# Test health endpoints
test_health_endpoint() {
    local service=$1
    local endpoint=$2
    
    log_info "Testing $service health endpoint..."
    
    if curl -sf "${BASE_URL}${endpoint}" > /dev/null 2>&1; then
        log_success "$service health check passed"
        return 0
    else
        log_error "$service health check failed"
        ((FAILURES++))
        return 1
    fi
}

# Test API endpoints
test_api_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local expected_status=${3:-200}
    
    log_info "Testing $method $endpoint..."
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "${BASE_URL}${endpoint}" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "$expected_status" ] || [ "$HTTP_CODE" = "401" ]; then
        # 401 is acceptable for protected endpoints
        log_success "$method $endpoint returned $HTTP_CODE"
        return 0
    else
        log_error "$method $endpoint returned $HTTP_CODE (expected $expected_status)"
        ((FAILURES++))
        return 1
    fi
}

# Test Kubernetes services
test_k8s_service() {
    local service=$1
    
    log_info "Checking Kubernetes service: $service"
    
    if kubectl get deployment "$service" -n gennet-system &> /dev/null; then
        READY=$(kubectl get deployment "$service" -n gennet-system -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        DESIRED=$(kubectl get deployment "$service" -n gennet-system -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
        
        if [ "$READY" = "$DESIRED" ] && [ "$READY" != "0" ]; then
            log_success "$service: $READY/$DESIRED replicas ready"
            return 0
        else
            log_error "$service: $READY/$DESIRED replicas ready (expected $DESIRED)"
            ((FAILURES++))
            return 1
        fi
    else
        log_error "$service deployment not found"
        ((FAILURES++))
        return 1
    fi
}

# Run health endpoint tests
log_info "=========================================="
log_info "Health Endpoint Tests"
log_info "=========================================="

test_health_endpoint "Auth Service" "/api/v1/auth/health"
test_health_endpoint "GRN Service" "/api/v1/networks/health"
test_health_endpoint "Workflow Service" "/api/v1/workflows/health"
test_health_endpoint "Qualitative Service" "/api/v1/qualitative/health"
test_health_endpoint "Hybrid Service" "/api/v1/hybrid/health"
test_health_endpoint "ML Service" "/api/v1/ml/health"

# Run API endpoint tests
echo ""
log_info "=========================================="
log_info "API Endpoint Tests"
log_info "=========================================="

test_api_endpoint "/api/v1/auth/token" "POST" "422"  # Expected: validation error without credentials
test_api_endpoint "/api/v1/networks" "GET" "401"     # Expected: unauthorized without token
test_api_endpoint "/api/v1/workflows" "GET" "401"    # Expected: unauthorized without token

# Run Kubernetes service tests
echo ""
log_info "=========================================="
log_info "Kubernetes Service Tests"
log_info "=========================================="

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

for service in "${SERVICES[@]}"; do
    test_k8s_service "$service"
done

# Summary
echo ""
log_info "=========================================="
log_info "Smoke Test Summary"
log_info "=========================================="
log_info "Failures: $FAILURES"
echo ""

if [ $FAILURES -eq 0 ]; then
    log_success "All smoke tests passed!"
    exit 0
else
    log_error "Smoke tests failed with $FAILURES failure(s)"
    exit 1
fi

