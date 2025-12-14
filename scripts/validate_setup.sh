#!/bin/bash
# Validation script to check setup

set -e

echo "Validating GenNet Platform Setup..."
echo "===================================="

# Check Python version
echo -n "Checking Python version... "
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "FAILED - Python $python_version found, $required_version+ required"
    exit 1
fi
echo "OK ($python_version)"

# Check Node.js version
echo -n "Checking Node.js version... "
if command -v node &> /dev/null; then
    node_version=$(node --version | sed 's/v//')
    echo "OK ($node_version)"
else
    echo "WARNING - Node.js not found (needed for frontend)"
fi

# Check Docker
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo "OK ($docker_version)"
else
    echo "WARNING - Docker not found (needed for containers)"
fi

# Check Terraform
echo -n "Checking Terraform... "
if command -v terraform &> /dev/null; then
    terraform_version=$(terraform version | head -n1 | awk '{print $2}' | sed 's/v//')
    echo "OK ($terraform_version)"
else
    echo "WARNING - Terraform not found (needed for infrastructure)"
fi

# Check kubectl
echo -n "Checking kubectl... "
if command -v kubectl &> /dev/null; then
    kubectl_version=$(kubectl version --client --short 2>&1 | awk '{print $3}')
    echo "OK ($kubectl_version)"
else
    echo "INFO - kubectl not found (optional for local dev)"
fi

# Check required Python packages
echo -n "Checking Python packages... "
if python3 -c "import fastapi, sqlalchemy, pytest" 2>/dev/null; then
    echo "OK"
else
    echo "WARNING - Some packages missing. Run: pip install -r requirements-dev.txt"
fi

# Check project structure
echo -n "Checking project structure... "
required_dirs=("services" "infrastructure" "frontend" "libraries")
all_present=true
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        all_present=false
        break
    fi
done

if [ "$all_present" = true ]; then
    echo "OK"
else
    echo "FAILED - Missing required directories"
    exit 1
fi

echo ""
echo "Validation complete!"
echo "===================================="

