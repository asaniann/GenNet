#!/bin/bash
# Clean virtual environment script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

if [ -d "venv" ]; then
    echo "Removing virtual environment..."
    rm -rf venv
    echo "Virtual environment removed."
    echo ""
    echo "To recreate, run: ./scripts/deploy.sh local"
else
    echo "No virtual environment found."
fi

