#!/bin/bash
# Security Scanning Script
# Runs security scans for dependencies and code

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

log_info "Running security scans..."
echo ""

# Check if tools are installed
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        log_warning "$1 not found. Install with: pip install $1"
        ((WARNINGS++))
        return 1
    fi
    return 0
}

# Run Safety (dependency vulnerability scanning)
log_info "Scanning Python dependencies for vulnerabilities..."
if check_tool safety; then
    if safety check --json > safety-report.json 2>&1; then
        log_success "No known vulnerabilities found"
    else
        log_warning "Some vulnerabilities detected. Review safety-report.json"
        ((WARNINGS++))
    fi
else
    log_warning "Safety not available. Skipping dependency scan."
fi

# Run Bandit (Python security linter)
log_info "Scanning Python code for security issues..."
if check_tool bandit; then
    if bandit -r services/ shared/ -f json -o bandit-report.json 2>&1; then
        # Check for high/critical issues
        HIGH_ISSUES=$(jq '.metrics.HIGH' bandit-report.json 2>/dev/null || echo "0")
        CRITICAL_ISSUES=$(jq '.metrics.CRITICAL' bandit-report.json 2>/dev/null || echo "0")
        
        if [ "$HIGH_ISSUES" = "0" ] && [ "$CRITICAL_ISSUES" = "0" ]; then
            log_success "No high or critical security issues found"
        else
            log_error "Found $HIGH_ISSUES high and $CRITICAL_ISSUES critical security issues"
            log_info "Review bandit-report.json for details"
            ((ERRORS++))
        fi
    else
        log_warning "Bandit scan completed with warnings"
        ((WARNINGS++))
    fi
else
    log_warning "Bandit not available. Skipping code security scan."
fi

# Summary
echo ""
log_info "=========================================="
log_info "Security Scan Summary"
log_info "=========================================="
log_info "Errors: $ERRORS"
log_info "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        log_success "All security scans passed!"
        exit 0
    else
        log_warning "Security scans completed with warnings. Review warnings above."
        exit 0
    fi
else
    log_error "Security scans failed with $ERRORS error(s). Fix issues before deployment."
    exit 1
fi

