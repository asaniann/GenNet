#!/bin/bash
# GenNet Cloud Platform - Undeployment Script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOYMENT_MODE="${1:-local}"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

undeploy_local() {
    log_info "Undeploying local services..."
    cd "$PROJECT_ROOT"
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down -v || docker compose down -v || log_warning "Failed to stop containers"
        log_success "Local services stopped and volumes removed"
    else
        log_warning "docker-compose.yml not found"
    fi
}

undeploy_production() {
    log_info "Undeploying production services..."
    
    # Remove Kubernetes resources
    if command -v kubectl &> /dev/null; then
        log_info "Removing Kubernetes resources..."
        kubectl delete all --all -n gennet-system 2>/dev/null || true
        kubectl delete namespace gennet-system 2>/dev/null || true
        log_success "Kubernetes resources removed"
    fi
    
    # Destroy Terraform infrastructure
    if [ -d "infrastructure/terraform" ]; then
        log_warning "This will destroy all infrastructure. Continue? (yes/no)"
        read -r confirmation
        if [ "$confirmation" = "yes" ]; then
            cd "$PROJECT_ROOT/infrastructure/terraform"
            terraform destroy || log_error "Terraform destroy failed"
            log_success "Infrastructure destroyed"
        else
            log_info "Cancelled"
        fi
    fi
}

if [ "$DEPLOYMENT_MODE" = "production" ]; then
    undeploy_production
else
    undeploy_local
fi

log_success "Undeployment complete!"

