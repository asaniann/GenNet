#!/bin/bash
# Install dependencies with Python version compatibility handling

set -e

echo "Installing dependencies..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "Python version: $(python3 --version)"

# Install dev dependencies first
echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# For Python 3.13, install compatible pydantic first to avoid build issues
if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo "Python 3.13 detected - installing compatible pydantic versions..."
    pip install --upgrade "pydantic>=2.10.0" "pydantic-core>=2.20.0"
    echo "Note: Service requirements may pin older pydantic versions."
    echo "      These will be skipped in favor of the compatible version."
fi

# Install service dependencies
# For Python 3.13, skip pydantic from service requirements to avoid conflicts
echo "Installing service dependencies..."
for req_file in services/*/requirements.txt; do
    if [ -f "$req_file" ]; then
        echo "Installing from $req_file..."
        if [[ "$PYTHON_VERSION" == "3.13" ]]; then
            # Filter out pydantic lines for Python 3.13
            pip install $(grep -v "^#" "$req_file" | grep -v "^$" | grep -v "^pydantic" | tr '\n' ' ') || \
            echo "Warning: Some dependencies from $req_file may have issues"
        else
            pip install -r "$req_file" || \
            echo "Warning: Some dependencies from $req_file may have issues"
        fi
    fi
done

echo ""
echo "Dependencies installed!"
if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo ""
    echo "⚠️  Python 3.13 detected - pydantic versions were upgraded for compatibility."
    echo "   Docker services use Python 3.11 and will work correctly."
    echo "   For best compatibility, consider using Python 3.11 for local development."
fi

