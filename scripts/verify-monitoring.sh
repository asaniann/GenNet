#!/bin/bash
# Monitoring Verification Script
# Verifies all monitoring, alerting, and dashboards are configured

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

log_info "Verifying monitoring setup for: $ENVIRONMENT"
echo ""

# Check Prometheus
log_info "Checking Prometheus..."
if kubectl get deployment prometheus -n monitoring &> /dev/null 2>&1; then
    PROM_READY=$(kubectl get deployment prometheus -n monitoring -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    if [ "$PROM_READY" != "0" ]; then
        log_success "Prometheus deployed ($PROM_READY replicas ready)"
        
        # Check if Prometheus is scraping
        if kubectl exec -n monitoring deployment/prometheus -- wget -qO- http://localhost:9090/api/v1/targets 2>/dev/null | grep -q "activeTargets"; then
            log_success "Prometheus is scraping targets"
        else
            log_warning "Prometheus targets not verified"
            ((WARNINGS++))
        fi
    else
        log_error "Prometheus not ready"
        ((ERRORS++))
    fi
else
    log_warning "Prometheus deployment not found (may need to deploy)"
    ((WARNINGS++))
fi

# Check Grafana
log_info "Checking Grafana..."
if kubectl get deployment grafana -n monitoring &> /dev/null 2>&1; then
    GRAFANA_READY=$(kubectl get deployment grafana -n monitoring -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    if [ "$GRAFANA_READY" != "0" ]; then
        log_success "Grafana deployed ($GRAFANA_READY replicas ready)"
        
        # Check dashboards
        if [ -d "infrastructure/monitoring/grafana/dashboards" ]; then
            DASHBOARD_COUNT=$(find infrastructure/monitoring/grafana/dashboards -name "*.json" | wc -l)
            log_success "Found $DASHBOARD_COUNT dashboard files"
        else
            log_warning "Grafana dashboards directory not found"
            ((WARNINGS++))
        fi
    else
        log_error "Grafana not ready"
        ((ERRORS++))
    fi
else
    log_warning "Grafana deployment not found (may need to deploy)"
    ((WARNINGS++))
fi

# Check Alertmanager
log_info "Checking Alertmanager..."
if kubectl get deployment alertmanager -n monitoring &> /dev/null 2>&1; then
    ALERT_READY=$(kubectl get deployment alertmanager -n monitoring -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    if [ "$ALERT_READY" != "0" ]; then
        log_success "Alertmanager deployed ($ALERT_READY replicas ready)"
    else
        log_error "Alertmanager not ready"
        ((ERRORS++))
    fi
else
    log_warning "Alertmanager deployment not found (may need to deploy)"
    ((WARNINGS++))
fi

# Check alert rules
log_info "Checking alert rules..."
if [ -f "infrastructure/monitoring/prometheus/alerts/services-alerts.yaml" ]; then
    ALERT_COUNT=$(grep -c "alert:" infrastructure/monitoring/prometheus/alerts/services-alerts.yaml 2>/dev/null || echo "0")
    log_success "Found $ALERT_COUNT alert rules"
else
    log_warning "Alert rules file not found"
    ((WARNINGS++))
fi

# Check service metrics
log_info "Checking service metrics endpoints..."
SERVICES=(
    "auth-service"
    "grn-service"
    "workflow-service"
    "qualitative-service"
    "hybrid-service"
    "ml-service"
    "health-service"
)

METRICS_COUNT=0
for service in "${SERVICES[@]}"; do
    if kubectl get deployment "$service" -n gennet-system &> /dev/null 2>&1; then
        # Check if service has metrics endpoint
        if kubectl exec -n gennet-system deployment/"$service" -- wget -qO- http://localhost:8000/metrics 2>/dev/null | grep -q "http_requests_total"; then
            log_success "$service metrics endpoint accessible"
            ((METRICS_COUNT++))
        else
            log_warning "$service metrics endpoint not accessible or not exposing metrics"
            ((WARNINGS++))
        fi
    fi
done

log_info "Metrics endpoints accessible: $METRICS_COUNT/${#SERVICES[@]}"

# Check logging
log_info "Checking logging configuration..."
if kubectl get daemonset fluentd -n logging &> /dev/null 2>&1 || kubectl get daemonset fluent-bit -n logging &> /dev/null 2>&1; then
    log_success "Logging daemonset found"
else
    log_warning "Logging daemonset not found (may need to deploy)"
    ((WARNINGS++))
fi

# Check tracing
log_info "Checking tracing configuration..."
if kubectl get deployment jaeger -n tracing &> /dev/null 2>&1; then
    JAEGER_READY=$(kubectl get deployment jaeger -n tracing -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    if [ "$JAEGER_READY" != "0" ]; then
        log_success "Jaeger deployed ($JAEGER_READY replicas ready)"
    else
        log_warning "Jaeger not ready"
        ((WARNINGS++))
    fi
else
    log_warning "Jaeger deployment not found (may need to deploy)"
    ((WARNINGS++))
fi

# Summary
echo ""
log_info "=========================================="
log_info "Monitoring Verification Summary"
log_info "=========================================="
log_info "Errors: $ERRORS"
log_info "Warnings: $WARNINGS"
log_info "Services with metrics: $METRICS_COUNT/${#SERVICES[@]}"
echo ""

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        log_success "All monitoring components verified!"
        exit 0
    else
        log_warning "Monitoring verified with warnings. Review warnings above."
        exit 0
    fi
else
    log_error "Monitoring verification failed with $ERRORS error(s). Fix errors before deployment."
    exit 1
fi

