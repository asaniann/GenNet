#!/bin/bash
# Script to add timeout handling to all Dockerfiles
# This adds --timeout and --retry flags to pip install commands

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Updating Dockerfiles with timeout handling..."

# Find all Dockerfiles
find services -name "Dockerfile" -type f | while read dockerfile; do
    echo "Processing $dockerfile..."
    
    # Check if already has timeout
    if grep -q "pip install.*--timeout" "$dockerfile"; then
        echo "  ✓ Already has timeout settings"
        continue
    fi
    
    # Update simple pip install -r requirements.txt (without timeout)
    if grep -q "^RUN pip install --no-cache-dir -r requirements.txt$" "$dockerfile"; then
        # Use a temporary file for multi-line replacement
        awk '
            /^RUN pip install --no-cache-dir -r requirements.txt$/ {
                print "RUN pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt || \\"
                print "    (echo \"Retrying pip install after timeout...\" && \\"
                print "     sleep 5 && \\"
                print "     pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt)"
                next
            }
            { print }
        ' "$dockerfile" > "${dockerfile}.tmp" && mv "${dockerfile}.tmp" "$dockerfile"
        echo "  ✓ Updated pip install command"
    fi
done

echo "Done! All Dockerfiles updated with timeout handling."

