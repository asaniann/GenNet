#!/bin/bash
# Quick script to restart deployment skipping heavy ML dependencies

echo "Restarting deployment with SKIP_SERVICE_DEPS=true to skip heavy ML dependencies..."
echo "This will skip PyTorch and other large packages (services use Docker containers anyway)"
echo ""

SKIP_SERVICE_DEPS=true ./scripts/deploy.sh local "$@"

