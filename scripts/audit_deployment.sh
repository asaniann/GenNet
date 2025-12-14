#!/bin/bash
# Deployment Readiness Audit Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

cd "$PROJECT_ROOT"

echo "=========================================="
echo "GenNet Platform - Deployment Readiness Audit"
echo "=========================================="
echo ""

# Track issues
ISSUES=0
WARNINGS=0

check_file() {
    if [ -f "$1" ]; then
        log_success "$1 exists"
        return 0
    else
        log_error "$1 MISSING"
        ((ISSUES++))
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        log_success "$1/ exists"
        return 0
    else
        log_error "$1/ MISSING"
        ((ISSUES++))
        return 1
    fi
}

check_service() {
    local service=$1
    local has_dockerfile=false
    local has_requirements=false
    local has_main=false
    local has_config=false
    
    if [ -f "services/$service/Dockerfile" ]; then
        has_dockerfile=true
    fi
    
    if [ -f "services/$service/requirements.txt" ]; then
        has_requirements=true
    fi
    
    if [ -f "services/$service/main.py" ]; then
        has_main=true
    fi
    
    # API Gateway is Kong-based (no main.py needed)
    if [ "$service" = "api-gateway" ]; then
        if [ -f "services/$service/kong.yml" ]; then
            has_config=true
        fi
        if $has_dockerfile && $has_config; then
            log_success "Service $service: Complete (Kong-based)"
            return 0
        else
            log_warning "Service $service: Missing components"
            ((WARNINGS++))
            return 1
        fi
    fi
    
    if $has_dockerfile && $has_main; then
        log_success "Service $service: Complete"
        return 0
    else
        log_warning "Service $service: Missing components"
        ((WARNINGS++))
        return 1
    fi
}

echo "1. CORE INFRASTRUCTURE"
echo "---------------------"
check_file "docker-compose.yml"
check_file "Makefile"
check_file "README.md"
check_file ".gitignore"
echo ""

echo "2. TERRAFORM INFRASTRUCTURE"
echo "---------------------------"
check_file "infrastructure/terraform/main.tf"
check_file "infrastructure/terraform/variables.tf"
check_file "infrastructure/terraform/outputs.tf"
check_file "infrastructure/terraform/terraform.tfvars.example"
check_dir "infrastructure/terraform/modules/vpc"
check_dir "infrastructure/terraform/modules/eks"
check_dir "infrastructure/terraform/modules/rds"
check_dir "infrastructure/terraform/modules/neptune"
check_dir "infrastructure/terraform/modules/s3"
check_dir "infrastructure/terraform/modules/redis"
echo ""

echo "3. KUBERNETES MANIFESTS"
echo "------------------------"
check_file "infrastructure/kubernetes/namespaces.yaml"
check_file "infrastructure/kubernetes/job-template.yaml"
check_file "infrastructure/kubernetes/backup-job.yaml"
check_file "infrastructure/kubernetes/configmap.yaml"
check_file "infrastructure/kubernetes/secrets-example.yaml"
check_file "infrastructure/kubernetes/auth-service-deployment.yaml"
check_file "infrastructure/kubernetes/grn-service-deployment.yaml"
check_file "infrastructure/kubernetes/workflow-service-deployment.yaml"
echo ""

echo "4. SERVICES"
echo "-----------"
SERVICES=(
    "api-gateway"
    "auth-service"
    "grn-service"
    "workflow-service"
    "qualitative-service"
    "hybrid-service"
    "ml-service"
    "collaboration-service"
    "metadata-service"
    "graphql-service"
    "hpc-orchestrator"
)

for service in "${SERVICES[@]}"; do
    check_service "$service"
done
echo ""

echo "5. FRONTEND"
echo "-----------"
check_dir "frontend/web"
check_file "frontend/web/package.json"
check_file "frontend/web/next.config.js"
check_file "frontend/web/Dockerfile"
echo ""

echo "6. PYTHON SDK"
echo "-------------"
check_dir "libraries/python-sdk"
check_file "libraries/python-sdk/setup.py"
check_dir "libraries/python-sdk/gennet"
echo ""

echo "7. TESTING"
echo "----------"
check_file "pytest.ini"
check_dir "services/auth-service/tests"
check_dir "services/grn-service/tests"
check_dir "services/workflow-service/tests"
check_dir "tests/integration"
check_dir "tests/performance"
echo ""

echo "8. DEPLOYMENT SCRIPTS"
echo "---------------------"
check_file "scripts/deploy.sh"
check_file "scripts/undeploy.sh"
check_file "scripts/validate_setup.sh"
check_file "scripts/run_tests.sh"
echo ""

echo "9. DOCUMENTATION"
echo "----------------"
check_file "docs/ARCHITECTURE.md"
check_file "docs/DEPLOYMENT_GUIDE.md"
check_file "docs/API.md"
check_file "docs/TESTING.md"
check_file "docs/TROUBLESHOOTING.md"
check_file "docs/COMPLETION_SUMMARY.md"
check_file "DEPLOYMENT_QUICKSTART.md"
echo ""

echo "10. MONITORING"
echo "--------------"
check_file "infrastructure/monitoring/prometheus.yml"
echo ""

echo "=========================================="
echo "AUDIT SUMMARY"
echo "=========================================="
echo "Issues found: $ISSUES"
echo "Warnings: $WARNINGS"
echo ""

if [ $ISSUES -eq 0 ]; then
    log_success "✓ Core infrastructure is complete!"
else
    log_error "✗ $ISSUES critical issues found"
fi

if [ $WARNINGS -gt 0 ]; then
    log_warning "! $WARNINGS warnings (non-critical)"
fi

exit $ISSUES

