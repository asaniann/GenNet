#!/bin/bash
# Secret Rotation Script
# Rotates secrets in AWS Secrets Manager and triggers External Secrets refresh

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

SECRET_NAME="${1:-}"
ROTATION_DAYS="${2:-90}"

if [ -z "$SECRET_NAME" ]; then
    log_error "Usage: $0 <secret-name> [rotation-days]"
    exit 1
fi

log_info "Rotating secret: $SECRET_NAME"

# Generate new secret value
if [[ "$SECRET_NAME" == *"password"* ]] || [[ "$SECRET_NAME" == *"Password"* ]]; then
    NEW_VALUE=$(openssl rand -base64 32)
elif [[ "$SECRET_NAME" == *"key"* ]] || [[ "$SECRET_NAME" == *"Key"* ]]; then
    NEW_VALUE=$(openssl rand -hex 32)
else
    NEW_VALUE=$(openssl rand -base64 24)
fi

# Update secret in AWS Secrets Manager
log_info "Updating secret in AWS Secrets Manager..."
aws secretsmanager update-secret \
    --secret-id "$SECRET_NAME" \
    --secret-string "$NEW_VALUE" \
    --rotation-rules "AutomaticallyAfterDays=$ROTATION_DAYS" \
    || {
        log_error "Failed to update secret"
        exit 1
    }

log_success "Secret rotated successfully"

# Trigger External Secrets refresh (if using External Secrets Operator)
if command -v kubectl &> /dev/null; then
    log_info "Triggering External Secrets refresh..."
    kubectl annotate externalsecret "$SECRET_NAME" \
        -n gennet-system \
        force-sync=$(date +%s) \
        --overwrite \
        || log_warning "Could not trigger External Secrets refresh (may not be installed)"
fi

log_success "Secret rotation complete"

