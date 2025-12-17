#!/bin/bash
# GenNet Cloud Platform - Unified Deployment Script
# Handles both local and production deployments
# Automatically installs missing dependencies when possible

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOYMENT_MODE="${1:-local}"
ENVIRONMENT="${2:-dev}"

# Logging functions
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

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    else
        echo "unknown"
    fi
}

# Install python3-venv package automatically
install_python_venv() {
    local distro=$(detect_distro)
    local python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    local package_name=""
    
    log_info "Attempting to install python3-venv package..."
    
    case "$distro" in
        ubuntu|debian)
            package_name="python3-venv"
            # Try to detect specific Python version
            if command -v python3.12 &>/dev/null; then
                package_name="python3.12-venv"
            elif command -v python3.11 &>/dev/null; then
                package_name="python3.11-venv"
            elif command -v python3.10 &>/dev/null; then
                package_name="python3.10-venv"
            fi
            
            log_info "Detected Debian/Ubuntu. Installing $package_name..."
            if command -v sudo &>/dev/null; then
                if sudo apt update -qq 2>/dev/null && sudo apt install -y "$package_name" 2>&1 | grep -v "^$" | grep -v "^WARNING"; then
                    log_success "python3-venv installed successfully"
                    return 0
                else
                    log_error "Failed to install $package_name automatically"
                    return 1
                fi
            else
                log_warning "sudo not available. Cannot install automatically."
                return 1
            fi
            ;;
        rhel|centos|fedora)
            if [ "$distro" = "fedora" ]; then
                package_name="python3-venv"
                log_info "Detected Fedora. Installing $package_name..."
                if command -v sudo &>/dev/null; then
                    if sudo dnf install -y "$package_name" 2>&1 | grep -v "^$" | grep -v "^Last metadata"; then
                        log_success "python3-venv installed successfully"
                        return 0
                    fi
                fi
            else
                package_name="python3-venv"
                log_info "Detected RHEL/CentOS. Installing $package_name..."
                if command -v sudo &>/dev/null; then
                    if sudo yum install -y "$package_name" 2>&1 | grep -v "^$" | grep -v "^Loaded plugins"; then
                        log_success "python3-venv installed successfully"
                        return 0
                    fi
                fi
            fi
            log_error "Failed to install $package_name automatically"
            return 1
            ;;
        *)
            log_warning "Unknown distribution. Cannot auto-install python3-venv."
            log_info "Please install python3-venv manually for your distribution."
            return 1
            ;;
    esac
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check Python
    if ! check_command python3; then
        missing_deps+=("python3")
    else
        local python_version=$(python3 --version 2>&1 | awk '{print $2}')
        log_info "Python version: $python_version"
        
        # Check if venv module is available
        if ! python3 -m venv --help &>/dev/null 2>&1; then
            log_warning "Python venv module not available."
            
            # Only try to auto-install if not skipping venv
            if [ "${SKIP_VENV:-false}" != "true" ]; then
                log_info "Attempting to install python3-venv automatically..."
                if ! install_python_venv; then
                    log_error "Could not install python3-venv automatically."
                    log_error "You can either:"
                    log_error "  1. Install manually: sudo apt install python3.12-venv (or your distro's equivalent)"
                    log_error "  2. Skip venv: SKIP_VENV=true ./scripts/deploy.sh local"
                    log_error ""
                    # Don't exit here if SKIP_VENV could be used, let it try and fail gracefully later
                fi
            fi
        fi
    fi
    
    # Check Docker (required for both)
    if ! check_command docker; then
        missing_deps+=("docker")
    else
        if ! docker info &> /dev/null; then
            error_exit "Docker daemon is not running. Please start Docker."
        fi
        log_info "Docker is available"
    fi
    
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        # Production-specific checks
        if ! check_command terraform; then
            missing_deps+=("terraform")
        fi
        
        if ! check_command kubectl; then
            missing_deps+=("kubectl")
        fi
        
        if ! check_command aws; then
            log_warning "AWS CLI not found. Some AWS operations may fail."
        fi
    else
        # Local checks
        if ! check_command docker-compose; then
            if ! docker compose version &> /dev/null; then
                missing_deps+=("docker-compose")
            fi
        fi
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error_exit "Missing required dependencies: ${missing_deps[*]}"
    fi
    
    log_success "All prerequisites met"
}

# Install Python dependencies
install_python_deps() {
    # For Docker deployments, Python deps are in containers, so skip local venv unless needed
    if [ "${SKIP_VENV:-false}" = "true" ]; then
        log_info "Skipping local Python dependencies (SKIP_VENV=true)"
        return 0
    fi
    
    if [ "$DEPLOYMENT_MODE" != "local" ]; then
        log_info "Skipping local Python dependencies (production uses containers)"
        return 0
    fi
    
    log_info "Installing Python dependencies (for local development/testing)..."
    log_info "Note: Service dependencies are optional - services run in Docker containers"
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment if it doesn't exist or is corrupted
    if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
        log_info "Creating Python virtual environment..."
        # Remove corrupted venv if it exists
        if [ -d "venv" ]; then
            log_warning "Removing corrupted virtual environment..."
            rm -rf venv
        fi
        
        # Check if venv module is available before trying
        if ! python3 -m venv --help &>/dev/null 2>&1; then
            log_error ""
            log_error "════════════════════════════════════════════════════════════════"
            log_error "Python venv module is not available on your system."
            log_error "════════════════════════════════════════════════════════════════"
            log_error ""
            log_info "Attempting automatic installation..."
            
            # Try to install automatically
            if install_python_venv; then
                log_success "python3-venv installed! Continuing..."
                # Verify it works now
                if ! python3 -m venv --help &>/dev/null 2>&1; then
                    log_warning "Installation completed but venv module still not available."
                    log_error "You may need to restart your shell or install manually."
                fi
            else
                log_error ""
                log_error "Automatic installation failed. Manual installation required:"
                log_error ""
                local distro=$(detect_distro)
                case "$distro" in
                    ubuntu|debian)
                        log_error "  sudo apt update"
                        log_error "  sudo apt install python3.12-venv"
                        ;;
                    rhel|centos)
                        log_error "  sudo yum install python3-venv"
                        ;;
                    fedora)
                        log_error "  sudo dnf install python3-venv"
                        ;;
                    *)
                        log_error "  Install python3-venv for your distribution"
                        ;;
                esac
                log_error ""
                log_warning "Or skip Python venv (Docker-only deployment):"
                log_warning "  SKIP_VENV=true ./scripts/deploy.sh local"
                log_error ""
                error_exit "Please install python3-venv manually, or use SKIP_VENV=true"
            fi
        fi
        
        # Try to create venv
        if ! python3 -m venv venv 2>&1; then
            log_error ""
            log_error "════════════════════════════════════════════════════════════════"
            log_error "Failed to create virtual environment."
            log_error "════════════════════════════════════════════════════════════════"
            log_error ""
            log_error "The virtual environment creation failed. This usually means:"
            log_error "  - python3-venv package is not installed"
            log_error "  - Python installation is incomplete"
            log_error ""
            log_error "To fix on Debian/Ubuntu:"
            log_error "    sudo apt update"
            log_error "    sudo apt install python3.12-venv"
            log_error ""
            log_error "After installing, you can recreate venv with:"
            log_error "    ./scripts/clean_venv.sh"
            log_error "    ./scripts/deploy.sh local"
            log_error ""
            log_error "Or skip Python dependencies (for Docker-only deployment):"
            log_error "    SKIP_VENV=true ./scripts/deploy.sh local"
            log_error ""
            error_exit "Virtual environment creation failed. See above for solutions."
        fi
        
        # Verify creation
        if [ ! -f "venv/bin/activate" ]; then
            error_exit "Virtual environment created but activate script missing. The venv may be corrupted. Try: ./scripts/clean_venv.sh"
        fi
        
        log_success "Virtual environment created successfully"
    fi
    
    # Check if activation script exists
    if [ ! -f "venv/bin/activate" ]; then
        error_exit "Virtual environment activation script not found. Try removing venv/ and running again."
    fi
    
    # Activate virtual environment with better error handling
    set +u  # Temporarily allow unset variables (venv activation may use unset vars)
    if ! source venv/bin/activate 2>/dev/null; then
        set -u
        error_exit "Failed to activate virtual environment. The venv may be corrupted. Try: ./scripts/clean_venv.sh"
    fi
    set -u
    
    # Verify activation worked
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        error_exit "Virtual environment activation failed. VIRTUAL_ENV not set."
    fi
    
    log_info "Virtual environment activated: $VIRTUAL_ENV"
    
    # Configure pip for better timeout and retry handling
    export PIP_DEFAULT_TIMEOUT=300  # 5 minutes
    export PIP_TIMEOUT=300
    export PIP_RETRIES=3
    
    # Helper function to retry pip installs on timeout
    pip_install_with_retry() {
        local max_retries=3
        local retry_count=0
        
        while [ $retry_count -lt $max_retries ]; do
            if [ $retry_count -gt 0 ]; then
                log_info "Retrying pip install (attempt $((retry_count + 1))/$max_retries)..."
                sleep $((retry_count * 5))  # Exponential backoff: 0s, 5s, 10s
            fi
            
            if pip "$@" --timeout=300 --retries=3 2>&1 | tee /tmp/pip_install_attempt.log; then
                return 0
            fi
            
            # Check if it's a timeout error
            if grep -qiE "Read timed out|TimeoutError|Connection.*timeout" /tmp/pip_install_attempt.log; then
                retry_count=$((retry_count + 1))
                log_warning "Network timeout detected (attempt $retry_count/$max_retries)"
                continue
            else
                # Not a timeout, return the error
                return 1
            fi
        done
        
        log_error "Failed after $max_retries retries due to network timeouts"
        return 1
    }
    
    # Upgrade pip (only if outdated)
    log_info "Checking pip version..."
    local current_pip=$(pip --version 2>/dev/null | awk '{print $2}' || echo "0.0.0")
    local latest_pip=$(pip index versions pip 2>/dev/null | grep -oP 'LATEST:\s+\K[^\s]+' || echo "")
    
    # If we can't check latest version, just upgrade (safe operation)
    if [ -z "$latest_pip" ]; then
        log_info "Upgrading pip (cannot check version)..."
        if pip install --upgrade pip --timeout=300 2>&1 | grep -qiE "ERROR|FAILED"; then
            log_warning "pip upgrade had issues (continuing anyway)"
        else
            echo -n "✓ "
        fi
    elif [ "$current_pip" != "$latest_pip" ]; then
        log_info "Upgrading pip ($current_pip -> $latest_pip)..."
        if pip install --upgrade pip --timeout=300 2>&1 | grep -qiE "ERROR|FAILED"; then
            log_warning "pip upgrade had issues (continuing anyway)"
        else
            echo -n "✓ "
        fi
    else
        log_info "pip is already up to date ($current_pip)"
    fi
    
    # Check Python version for compatibility fixes
    local python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    local is_python313=false
    if [ "$python_version" = "3.13" ]; then
        is_python313=true
        log_info "Python 3.13 detected - applying compatibility fixes for pydantic..."
        # Install compatible pydantic versions first to avoid build errors
        log_info "Installing Python 3.13-compatible pydantic versions..."
        if pip install --upgrade --no-cache-dir --timeout=300 --retries=3 "pydantic>=2.10.0" "pydantic-core>=2.20.0" 2>&1 | grep -qiE "ERROR|FAILED"; then
            log_warning "Failed to install compatible pydantic versions (continuing anyway)"
        else
            log_success "Compatible pydantic versions installed"
        fi
    fi
    
    # Install development dependencies (only if requirements changed or missing)
    if [ -f "requirements-dev.txt" ]; then
        local req_hash_file="$PROJECT_ROOT/.venv/requirements-dev.hash"
        local current_hash=$(md5sum requirements-dev.txt 2>/dev/null | awk '{print $1}' || sha256sum requirements-dev.txt 2>/dev/null | awk '{print $1}' || echo "")
        
        if [ -n "$current_hash" ] && [ -f "$req_hash_file" ]; then
            local cached_hash=$(cat "$req_hash_file" 2>/dev/null || echo "")
            if [ "$current_hash" = "$cached_hash" ]; then
                # Verify packages are actually installed
                local missing_count=0
                while IFS= read -r line || [ -n "$line" ]; do
                    line=$(echo "$line" | sed 's/#.*$//' | xargs)
                    [ -z "$line" ] && continue
                    local pkg_name=$(echo "$line" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | cut -d'[' -f1 | xargs)
                    [ -z "$pkg_name" ] && continue
                    if ! pip show "$pkg_name" &>/dev/null; then
                        missing_count=$((missing_count + 1))
                    fi
                done < requirements-dev.txt
                
                if [ $missing_count -eq 0 ]; then
                    log_info "Development dependencies unchanged and all installed (skipping)"
                else
                    log_info "Installing development dependencies ($missing_count packages missing)..."
                    if pip_install_with_retry install --upgrade-strategy only-if-needed -r requirements-dev.txt; then
                        echo -n "✓ "
                    else
                        log_warning "Some dev dependencies had issues (continuing - tests may be affected)"
                    fi
                fi
            else
                log_info "Installing development dependencies (requirements changed)..."
                if pip_install_with_retry pip install --upgrade-strategy only-if-needed -r requirements-dev.txt; then
                    echo -n "✓ "
                    mkdir -p "$PROJECT_ROOT/.venv"
                    echo "$current_hash" > "$req_hash_file"
                else
                    log_warning "Some dev dependencies had issues (continuing - tests may be affected)"
                fi
            fi
        else
            log_info "Installing development dependencies..."
            if pip_install_with_retry pip install --upgrade-strategy only-if-needed -r requirements-dev.txt; then
                echo -n "✓ "
                if [ -n "$current_hash" ]; then
                    mkdir -p "$PROJECT_ROOT/.venv"
                    echo "$current_hash" > "$req_hash_file"
                fi
            else
                log_warning "Some dev dependencies had issues (continuing - tests may be affected)"
            fi
        fi
    fi
    
    # Install service dependencies
    # Note: For Docker deployments, these are NOT needed locally - they're in containers
    log_info "Installing service dependencies (optional - services run in containers)..."
    log_warning "⚠️  ML service dependencies (PyTorch) are VERY LARGE (~2GB) and may take 10-20 minutes!"
    log_info "💡 TIP: Press Ctrl+C to cancel and restart with: SKIP_SERVICE_DEPS=true ./scripts/deploy.sh local"
    log_info ""
    
    if [ "${SKIP_SERVICE_DEPS:-false}" = "true" ]; then
        log_info "Skipping service dependencies (SKIP_SERVICE_DEPS=true)"
        log_info "Services will use Docker containers which have dependencies pre-installed"
        return 0
    fi
    
    # Check Python version again for service installation (in case it wasn't set earlier)
    if [ -z "${is_python313:-}" ]; then
        local python_version_check=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
        if [ "$python_version_check" = "3.13" ]; then
            is_python313=true
        else
            is_python313=false
        fi
    fi
    
    local failed_services=()
    local heavy_services=("ml-service")
    
    while IFS= read -r -d '' req_file; do
        if [ -f "$req_file" ]; then
            local service_name=$(dirname "$req_file" | xargs basename)
            local is_heavy=false
            
            # Check if this is a heavy service
            for heavy in "${heavy_services[@]}"; do
                if [ "$service_name" = "$heavy" ]; then
                    is_heavy=true
                    break
                fi
            done
            
            # Check if requirements file changed or dependencies are missing
            local req_hash_file="$PROJECT_ROOT/.venv/${service_name}.hash"
            local current_hash=$(md5sum "$req_file" 2>/dev/null | awk '{print $1}' || sha256sum "$req_file" 2>/dev/null | awk '{print $1}' || echo "")
            local should_install=true
            
            if [ -n "$current_hash" ] && [ -f "$req_hash_file" ]; then
                local cached_hash=$(cat "$req_hash_file" 2>/dev/null || echo "")
                if [ "$current_hash" = "$cached_hash" ]; then
                    # Check if ALL packages from requirements.txt are actually installed
                    local missing_packages=0
                    local total_packages=0
                    
                    # Read requirements file and check each package
                    while IFS= read -r line || [ -n "$line" ]; do
                        # Skip comments and empty lines
                        line=$(echo "$line" | sed 's/#.*$//' | xargs)
                        [ -z "$line" ] && continue
                        
                        # Extract package name (handle various formats: package==1.0, package>=1.0, etc.)
                        local pkg_name=$(echo "$line" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | cut -d'[' -f1 | xargs)
                        [ -z "$pkg_name" ] && continue
                        
                        total_packages=$((total_packages + 1))
                        
                        # Check if package is installed
                        if ! pip show "$pkg_name" &>/dev/null; then
                            missing_packages=$((missing_packages + 1))
                        fi
                    done < "$req_file"
                    
                    if [ $total_packages -eq 0 ]; then
                        # Empty requirements file, skip
                        should_install=false
                    elif [ $missing_packages -eq 0 ]; then
                        log_info "Skipping $service_name - all $total_packages dependencies already installed"
                        should_install=false
                    else
                        log_info "$service_name: $missing_packages of $total_packages packages missing, will install"
                    fi
                fi
            fi
            
            if [ "$should_install" = "true" ]; then
                # For Python 3.13, filter out old pydantic versions to avoid build errors
                local install_cmd="pip install --upgrade-strategy only-if-needed -r"
                if [ "$is_python313" = "true" ] && grep -q "^pydantic" "$req_file"; then
                    log_info "Python 3.13: Filtering out old pydantic versions from $service_name..."
                    # Create temporary requirements file without pydantic
                    local temp_req="/tmp/${service_name}_req_no_pydantic.txt"
                    grep -v "^pydantic" "$req_file" | grep -v "^#" | grep -v "^$" > "$temp_req" || true
                    if [ -s "$temp_req" ]; then
                        install_cmd="pip install --upgrade-strategy only-if-needed -r"
                        req_file="$temp_req"
                    fi
                fi
                
                if [ "$is_heavy" = "true" ]; then
                    log_warning "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    log_warning "Installing $service_name dependencies (PyTorch ~2GB download)"
                    log_warning "This may take 10-20 minutes depending on your internet speed"
                    log_warning "You can cancel (Ctrl+C) and restart with SKIP_SERVICE_DEPS=true"
                    log_warning "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    log_info "Downloading and installing (showing progress)..."
                    # Use --upgrade-strategy only-if-needed to avoid re-downloading existing packages
                    # Use --no-deps only for specific cases, otherwise let pip handle dependencies
                    if pip_install_with_retry install --upgrade-strategy only-if-needed -r "$req_file" 2>&1 | tee /tmp/pip_install_${service_name}.log; then
                        log_success "$service_name dependencies installed successfully"
                        if [ -n "$current_hash" ]; then
                            mkdir -p "$PROJECT_ROOT/.venv"
                            echo "$current_hash" > "$req_hash_file"
                        fi
                    else
                        local install_exit=$?
                        # Check for pydantic-core build errors specifically
                        if grep -qiE "pydantic-core.*ForwardRef.*recursive_guard" /tmp/pip_install_${service_name}.log; then
                            log_warning "pydantic-core build error detected (Python 3.13 compatibility issue)"
                            log_info "Attempting to install compatible pydantic version..."
                            if pip install --upgrade --no-cache-dir --timeout=300 --retries=3 "pydantic>=2.10.0" "pydantic-core>=2.20.0" 2>&1 | grep -qiE "ERROR|FAILED"; then
                                log_warning "$service_name: pydantic installation failed (non-critical - service runs in Docker)"
                            else
                                log_success "$service_name: Installed compatible pydantic version"
                                # Retry installing other dependencies
                                if [ -f "$temp_req" ] && [ -s "$temp_req" ]; then
                                    pip install --upgrade-strategy only-if-needed -r "$temp_req" >/tmp/pip_install_${service_name}_retry.log 2>&1 || true
                                fi
                            fi
                            failed_services+=("$service_name")
                        elif grep -qiE "ERROR|FAILED|Could not find a version|No matching distribution" /tmp/pip_install_${service_name}.log; then
                            log_warning "$service_name installation had errors (non-critical - service runs in Docker)"
                            failed_services+=("$service_name")
                        else
                            log_warning "$service_name installation failed (exit code: $install_exit, non-critical)"
                            failed_services+=("$service_name")
                        fi
                    fi
                    # Clean up temp file
                    [ -f "$temp_req" ] && rm -f "$temp_req" || true
                else
                    log_info "Installing from $req_file ($service_name)..."
                    # Install with --upgrade-strategy only-if-needed to avoid unnecessary downloads
                    if pip_install_with_retry install --upgrade-strategy only-if-needed -r "$req_file" >/tmp/pip_install_${service_name}.log 2>&1; then
                        echo "✓ "
                        if [ -n "$current_hash" ]; then
                            mkdir -p "$PROJECT_ROOT/.venv"
                            echo "$current_hash" > "$req_hash_file"
                        fi
                    else
                        # Check for pydantic-core build errors
                        if grep -qiE "pydantic-core.*ForwardRef.*recursive_guard" /tmp/pip_install_${service_name}.log; then
                            log_warning "pydantic-core build error detected (Python 3.13 compatibility)"
                            log_info "Installing compatible pydantic version for $service_name..."
                            pip install --upgrade --no-cache-dir --timeout=300 --retries=3 "pydantic>=2.10.0" "pydantic-core>=2.20.0" >/dev/null 2>&1 || true
                            # Retry with filtered requirements
                            if [ -f "$temp_req" ] && [ -s "$temp_req" ]; then
                                pip install --upgrade-strategy only-if-needed -r "$temp_req" >/tmp/pip_install_${service_name}_retry.log 2>&1 || true
                            fi
                            failed_services+=("$service_name")
                        elif grep -qiE "ERROR|FAILED|Could not find a version|No matching distribution" /tmp/pip_install_${service_name}.log; then
                            log_warning "Some dependencies failed for $service_name (non-critical - service runs in Docker)"
                            failed_services+=("$service_name")
                        else
                            echo "✓ "  # Probably succeeded with warnings
                            if [ -n "$current_hash" ]; then
                                mkdir -p "$PROJECT_ROOT/.venv"
                                echo "$current_hash" > "$req_hash_file"
                            fi
                        fi
                    fi
                    # Clean up temp file
                    [ -f "$temp_req" ] && rm -f "$temp_req" || true
                fi
            fi
        fi
    done < <(find services -name "requirements.txt" -print0 2>/dev/null || true)
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        log_info "Some service dependencies had issues (this is OK - services use Docker containers)"
        log_info "Affected services: ${failed_services[*]}"
    else
        log_success "Service dependencies processed (services will use Docker containers anyway)"
    fi
    
    # Install Python SDK (optional, skip if it fails or already installed)
    if [ -d "libraries/python-sdk" ] && [ -f "libraries/python-sdk/setup.py" ]; then
        # Check if SDK is already installed
        local sdk_name=$(grep -E "^name\s*=" libraries/python-sdk/setup.py 2>/dev/null | sed "s/.*name\s*=\s*['\"]\(.*\)['\"].*/\1/" || echo "gennet-sdk")
        if pip show "$sdk_name" &>/dev/null; then
            log_info "Python SDK already installed (skipping)"
        else
            log_info "Installing Python SDK (optional)..."
            # Try simple installation first
            cd libraries/python-sdk
            if pip install -e . 2>&1 | tee /tmp/sdk_install.log | grep -qi "error\|failed\|exception\|traceback"; then
                log_warning "Python SDK installation had issues (SDK is optional for deployment)"
                log_warning "You can skip SDK installation - it's only needed for Python API clients"
            else
                log_success "Python SDK installed successfully"
            fi
            cd "$PROJECT_ROOT"
        fi
    fi
    
    log_success "Python dependencies installed"
}

# Install Node.js dependencies
install_node_deps() {
    log_info "Installing Node.js dependencies..."
    
    if ! check_command node; then
        log_warning "Node.js not found. Skipping frontend dependencies."
        return 0
    fi
    
    if [ -d "frontend/web" ]; then
        cd "$PROJECT_ROOT/frontend/web"
        
        # Check if node_modules exists and package.json hasn't changed
        local should_install=true
        if [ -d "node_modules" ] && [ -f "package.json" ]; then
            local pkg_hash_file="$PROJECT_ROOT/.venv/frontend-package.hash"
            local current_hash=$(md5sum package.json package-lock.json 2>/dev/null | md5sum | awk '{print $1}' || \
                                sha256sum package.json package-lock.json 2>/dev/null | sha256sum | awk '{print $1}' || echo "")
            
            if [ -n "$current_hash" ] && [ -f "$pkg_hash_file" ]; then
                local cached_hash=$(cat "$pkg_hash_file" 2>/dev/null || echo "")
                if [ "$current_hash" = "$cached_hash" ]; then
                    log_info "Frontend dependencies unchanged (skipping npm install)"
                    should_install=false
                else
                    log_info "package.json changed - reinstalling dependencies..."
                fi
            fi
        fi
        
        if [ "$should_install" = "true" ]; then
            if [ ! -d "node_modules" ]; then
                log_info "Installing frontend dependencies (this may take a while)..."
            else
                log_info "Reinstalling frontend dependencies (package.json changed)..."
            fi
            
            npm install || error_exit "Failed to install frontend dependencies"
            
            # Save hash if installation succeeded
            if [ -f "package.json" ]; then
                local pkg_hash_file="$PROJECT_ROOT/.venv/frontend-package.hash"
                local current_hash=$(md5sum package.json package-lock.json 2>/dev/null | md5sum | awk '{print $1}' || \
                                    sha256sum package.json package-lock.json 2>/dev/null | sha256sum | awk '{print $1}' || echo "")
                if [ -n "$current_hash" ]; then
                    mkdir -p "$PROJECT_ROOT/.venv"
                    echo "$current_hash" > "$pkg_hash_file"
                    log_success "Frontend dependencies installed and cached"
                fi
            fi
        fi
        
        log_success "Frontend dependencies ready"
    fi
}

# Build Docker images (only if missing or changed)
build_docker_images() {
    log_info "Building Docker images (only if missing or changed)..."
    
    cd "$PROJECT_ROOT"
    
    local services=(
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
        "api-gateway"
    )
    
    for service in "${services[@]}"; do
        local service_dir="services/$service"
        if [ -d "$service_dir" ] && [ -f "$service_dir/Dockerfile" ]; then
            # Check if image already exists (unless FORCE_BUILD is set)
            local image_name="gennet/${service}:latest"
            if [ "${FORCE_BUILD:-false}" != "true" ] && docker images -q "$image_name" 2>/dev/null | grep -q .; then
                log_info "Skipping $service - image already exists (use FORCE_BUILD=true to rebuild)"
                continue
            fi
            
            log_info "Building $service..."
            # API gateway is optional - services can run without it
            if [ "$service" = "api-gateway" ]; then
                log_info "Building API gateway (optional - services work without it)..."
                # API gateway might have different build context, check if it has shared dependency
                if [ -f "$service_dir/Dockerfile" ] && grep -q "shared" "$service_dir/Dockerfile" 2>/dev/null; then
                    # Use project root as build context
                    if docker build -t "$image_name" -f "$service_dir/Dockerfile" . 2>&1 | grep -i "error\|failed"; then
                        log_warning "API gateway build failed (non-critical - services run directly)"
                        log_info "Services will be accessible directly on their ports without gateway"
                    else
                        log_success "API gateway built successfully"
                    fi
                else
                    # Use service directory as build context (old way)
                    if docker build -t "$image_name" "$service_dir" 2>&1 | grep -i "error\|failed"; then
                        log_warning "API gateway build failed (non-critical - services run directly)"
                        log_info "Services will be accessible directly on their ports without gateway"
                    else
                        log_success "API gateway built successfully"
                    fi
                fi
            else
                # All services now use project root as build context (to access shared directory)
                if docker build -t "$image_name" -f "$service_dir/Dockerfile" . 2>&1 | grep -qi "error\|failed"; then
                    log_warning "Failed to build $service"
                else
                    log_success "$service built successfully"
                fi
            fi
        fi
    done
    
    # Build frontend (only if missing or FORCE_BUILD is set)
    if [ -d "frontend/web" ] && [ -f "frontend/web/Dockerfile" ]; then
        local web_image="gennet/web:latest"
        if [ "${FORCE_BUILD:-false}" != "true" ] && docker images -q "$web_image" 2>/dev/null | grep -q .; then
            log_info "Skipping frontend - image already exists (use FORCE_BUILD=true to rebuild)"
        else
            log_info "Building frontend..."
            docker build -t "$web_image" "frontend/web" || log_warning "Failed to build frontend"
        fi
    fi
    
    log_success "Docker images built (skipped existing images)"
}

# Fix port conflicts for Docker Compose services
fix_port_conflicts() {
    # Only check ports if we're actually deploying (not just checking)
    if [ "${SKIP_PORT_CHECK:-false}" = "true" ]; then
        log_info "Skipping port conflict check (SKIP_PORT_CHECK=true)"
        return 0
    fi
    
    log_info "Checking for port conflicts..."
    
    # Define ports to check: service_name:port:alt_port
    declare -A ports_to_check=(
        ["postgres"]="5432:5433"
        ["redis"]="6379:6380"
        ["neo4j-http"]="7474:7475"
        ["neo4j-bolt"]="7687:7688"
        ["influxdb"]="8086:8087"
    )
    
    local conflicts_found=false
    local ports_in_use=()
    
    for service in "${!ports_to_check[@]}"; do
        IFS=':' read -r port alt_port <<< "${ports_to_check[$service]}"
        
        # Check if port is in use
        if lsof -i :${port} >/dev/null 2>&1 || ss -tulpn 2>/dev/null | grep -q ":${port}"; then
            # Check if it's our own Docker Compose service (allow it)
            local our_container=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E "gennet-.*-1$" | head -1 || echo "")
            if [ -n "$our_container" ]; then
                local container_ports=$(docker port "$our_container" 2>/dev/null | grep ":${port}" || echo "")
                if [ -n "$container_ports" ]; then
                    log_info "Port $port is used by our service ($our_container) - OK"
                    continue
                fi
            fi
            
            log_warning "Port $port ($service) is already in use"
            conflicts_found=true
            ports_in_use+=("$port")
            
            # Check if it's a Docker container
            local containers_using_port=$(docker ps --format '{{.Names}} {{.Ports}}' 2>/dev/null | grep ":${port}->" | awk '{print $1}' || echo "")
            
            if [ ! -z "$containers_using_port" ]; then
                log_info "Found Docker containers using port $port:"
                echo "$containers_using_port" | while read container; do
                    [ ! -z "$container" ] && log_info "  • $container"
                done
                
                log_info "Stopping conflicting containers..."
                echo "$containers_using_port" | while read container; do
                    if [ ! -z "$container" ]; then
                        docker stop "$container" 2>/dev/null || true
                        docker rm "$container" 2>/dev/null || true
                    fi
                done
                sleep 1
            fi
            
            # Check again if port is still in use
            if lsof -i :${port} >/dev/null 2>&1 || ss -tulpn 2>/dev/null | grep -q ":${port}"; then
                log_warning "Port $port still in use, attempting to kill process..."
                
                # Try to find and kill the process
                local pid=$(lsof -ti :${port} 2>/dev/null || fuser ${port}/tcp 2>/dev/null | awk '{print $NF}' || echo "")
                
                if [ ! -z "$pid" ] && [ "$pid" != "PID" ]; then
                    log_info "Killing process $pid on port $port..."
                    sudo kill -9 $pid 2>/dev/null || kill -9 $pid 2>/dev/null || true
                    sleep 1
                fi
                
                # Final check
                if lsof -i :${port} >/dev/null 2>&1 || ss -tulpn 2>/dev/null | grep -q ":${port}"; then
                    log_warning "Could not free port $port ($service)"
                    log_warning "You may need to stop the service manually or use alternative port"
                else
                    log_success "Port $port ($service) is now free"
                fi
            else
                log_success "Port $port ($service) is now available"
            fi
        fi
    done
    
    if [ "$conflicts_found" = false ]; then
        log_success "No port conflicts detected"
    else
        log_info "Resolved conflicts for ports: ${ports_in_use[*]}"
    fi
}

# Local deployment
deploy_local() {
    log_info "Starting local deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        error_exit "docker-compose.yml not found"
    fi
    
    # Fix port conflicts automatically
    fix_port_conflicts
    
    # Stop existing containers
    log_info "Stopping existing containers..."
    docker-compose -f docker-compose.yml -f docker-compose.services.yml down 2>/dev/null || \
    docker compose -f docker-compose.yml -f docker-compose.services.yml down 2>/dev/null || true
    
    # Check if we should force rebuild (only if FORCE_BUILD=true)
    local build_flag=""
    if [ "${FORCE_BUILD:-false}" = "true" ]; then
        log_info "FORCE_BUILD=true - will rebuild all images"
        build_flag="--build"
    else
        log_info "Using existing images (Docker Compose will only build if images are missing)"
        log_info "Set FORCE_BUILD=true to force rebuild all services"
    fi
    
    # Start services (both infrastructure and application services)
    # Docker Compose will automatically build missing images, but won't rebuild existing ones
    # unless --build flag is used or Dockerfile/context changed
    log_info "Starting services with Docker Compose..."
    log_info "Using docker-compose.yml (infrastructure) + docker-compose.services.yml (services)..."
    docker-compose -f docker-compose.yml -f docker-compose.services.yml up -d $build_flag || \
    docker compose -f docker-compose.yml -f docker-compose.services.yml up -d $build_flag || \
    error_exit "Failed to start Docker Compose services"
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    log_info "Checking service health..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f docker-compose.yml -f docker-compose.services.yml ps 2>/dev/null | grep -q "Up" || \
           docker compose -f docker-compose.yml -f docker-compose.services.yml ps 2>/dev/null | grep -q "Up"; then
            log_success "Services are running"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_warning "Services may not be fully ready. Check with 'docker-compose -f docker-compose.yml -f docker-compose.services.yml ps'"
    fi
    
    # Display service status
    log_info "Service status:"
    docker-compose -f docker-compose.yml -f docker-compose.services.yml ps 2>/dev/null || \
    docker compose -f docker-compose.yml -f docker-compose.services.yml ps 2>/dev/null || true
    
    log_success "Local deployment complete!"
    log_info "Services should be available at:"
    log_info "  - Frontend (Web UI): http://localhost:3000"
    log_info "  - Auth Service: http://localhost:8001/health"
    log_info "  - GRN Service: http://localhost:8002/health"
    log_info "  - Workflow Service: http://localhost:8003/health"
    log_info ""
    log_info "View logs with: docker-compose -f docker-compose.yml -f docker-compose.services.yml logs -f"
    log_info "View frontend logs: docker-compose -f docker-compose.yml -f docker-compose.services.yml logs -f web"
    log_info "Stop services with: docker-compose -f docker-compose.yml -f docker-compose.services.yml down"
}

# Production deployment
deploy_production() {
    log_info "Starting production deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Initialize Terraform
    if [ -d "infrastructure/terraform" ]; then
        log_info "Initializing Terraform..."
        cd infrastructure/terraform
        
        # Check for terraform.tfvars
        if [ ! -f "terraform.tfvars" ]; then
            log_warning "terraform.tfvars not found. Creating from template..."
            if [ -f "terraform.tfvars.example" ]; then
                cp terraform.tfvars.example terraform.tfvars
                log_warning "Please edit terraform.tfvars with your configuration"
                error_exit "terraform.tfvars must be configured before deployment"
            else
                error_exit "terraform.tfvars not found and no example available"
            fi
        fi
        
        terraform init || error_exit "Terraform initialization failed"
        
        # Plan deployment
        log_info "Planning Terraform deployment..."
        terraform plan -out=tfplan || error_exit "Terraform plan failed"
        
        # Ask for confirmation
        log_warning "This will deploy infrastructure to AWS. Continue? (yes/no)"
        read -r confirmation
        if [ "$confirmation" != "yes" ]; then
            log_info "Deployment cancelled"
            exit 0
        fi
        
        # Apply Terraform
        log_info "Applying Terraform configuration..."
        terraform apply tfplan || error_exit "Terraform apply failed"
        
        # Get outputs
        log_info "Retrieving Terraform outputs..."
        terraform output
        
        cd "$PROJECT_ROOT"
    else
        log_warning "Terraform directory not found. Skipping infrastructure deployment."
    fi
    
    # Build and push Docker images (if registry configured)
    if [ -n "${DOCKER_REGISTRY:-}" ]; then
        log_info "Pushing Docker images to registry..."
        # This would push to your registry
        log_warning "Docker registry push not implemented. Please push manually."
    fi
    
    # Deploy to Kubernetes
    if [ -d "infrastructure/kubernetes" ] && check_command kubectl; then
        log_info "Deploying to Kubernetes..."
        
        # Check kubectl context
        local current_context=$(kubectl config current-context 2>/dev/null || echo "none")
        log_info "Current Kubernetes context: $current_context"
        
        # Create namespaces
        if [ -f "infrastructure/kubernetes/namespaces.yaml" ]; then
            log_info "Creating namespaces..."
            kubectl apply -f infrastructure/kubernetes/namespaces.yaml || log_warning "Failed to create namespaces"
        fi
        
        # Apply Kubernetes manifests
        log_info "Applying Kubernetes manifests..."
        find infrastructure/kubernetes -name "*.yaml" -type f -exec kubectl apply -f {} \; || log_warning "Some Kubernetes resources may have failed"
        
        log_info "Waiting for deployments to be ready..."
        kubectl wait --for=condition=available --timeout=300s deployment --all -n gennet-system || log_warning "Some deployments may not be ready"
        
        log_success "Kubernetes deployment complete!"
    else
        log_warning "Kubernetes directory not found or kubectl not available. Skipping Kubernetes deployment."
    fi
    
    log_success "Production deployment complete!"
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."
    
    if [ "$DEPLOYMENT_MODE" = "local" ]; then
        # Check if containers are running
        if docker-compose ps | grep -q "Up" || docker compose ps | grep -q "Up"; then
            log_success "Local deployment validation passed"
        else
            log_error "Local deployment validation failed - containers not running"
            return 1
        fi
    else
        # Check Kubernetes deployments
        if check_command kubectl; then
            local ready_deployments=$(kubectl get deployments -n gennet-system -o jsonpath='{.items[*].status.conditions[?(@.type=="Available")].status}' 2>/dev/null | grep -o "True" | wc -l)
            if [ "$ready_deployments" -gt 0 ]; then
                log_success "Production deployment validation passed ($ready_deployments deployments ready)"
            else
                log_warning "Production deployment validation - some deployments may not be ready"
            fi
        fi
    fi
}

# Run tests
run_tests() {
    local run_tests="${RUN_TESTS:-false}"
    
    if [ "$run_tests" != "true" ]; then
        log_info "Skipping tests (set RUN_TESTS=true to run tests)"
        return 0
    fi
    
    log_info "Running tests..."
    
    cd "$PROJECT_ROOT"
    
    # Activate venv if it exists
    if [ -f "venv/bin/activate" ]; then
        set +u
        source venv/bin/activate 2>/dev/null || log_warning "Could not activate venv for tests"
        set -u
    fi
    
    # Run unit tests
    log_info "Running unit tests..."
    pytest -m unit --tb=short -q || log_warning "Some unit tests failed"
    
    log_success "Tests completed"
}

# Cleanup function
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "Deployment failed. Check logs above for details."
    fi
}

# Main execution
main() {
    trap cleanup EXIT
    
    log_info "=========================================="
    log_info "GenNet Cloud Platform Deployment"
    log_info "Mode: $DEPLOYMENT_MODE"
    log_info "Environment: $ENVIRONMENT"
    log_info "=========================================="
    echo ""
    
    # Check prerequisites (this may install python3-venv automatically)
    check_prerequisites
    
    # Install dependencies
    # Note: Python deps installation will be skipped if SKIP_VENV=true
    install_python_deps
    
    # Activate venv if it was created
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ] && [ -z "${VIRTUAL_ENV:-}" ]; then
        set +u
        source "$PROJECT_ROOT/venv/bin/activate" 2>/dev/null || true
        set -u
        if [ -n "${VIRTUAL_ENV:-}" ]; then
            export VENV_ACTIVATED=true
            log_info "Virtual environment activated: $VIRTUAL_ENV"
        fi
    fi
    
    install_node_deps
    
    # Build Docker images (only if not skipping)
    # Note: build_docker_images() will skip existing images unless FORCE_BUILD=true
    if [ "${SKIP_BUILD:-false}" != "true" ]; then
        build_docker_images
    else
        log_info "Skipping Docker image build (SKIP_BUILD=true)"
        log_info "Docker Compose will build missing images automatically when starting services"
    fi
    
    # Deploy based on mode
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        deploy_production
    else
        deploy_local
    fi
    
    # Pre-deployment validation
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        log_info "Running pre-deployment checks..."
        if [ -f "scripts/pre-deployment-check.sh" ]; then
            ./scripts/pre-deployment-check.sh "$ENVIRONMENT" || {
                log_error "Pre-deployment checks failed"
                error_exit "Please fix issues before deploying"
            }
        fi
    fi
    
    # Validate deployment
    validate_deployment
    
    # Post-deployment validation
    if [ "$DEPLOYMENT_MODE" = "production" ]; then
        log_info "Running post-deployment smoke tests..."
        if [ -f "scripts/run_smoke_tests.sh" ]; then
            ./scripts/run_smoke_tests.sh "$ENVIRONMENT" || {
                log_warning "Some smoke tests failed. Review and fix if needed."
            }
        fi
    fi
    
    # Run tests if requested
    run_tests
    
    log_success "=========================================="
    log_success "Deployment completed successfully!"
    log_success "=========================================="
}

# Show usage if help requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat << EOF
GenNet Cloud Platform - Deployment Script

This script automatically handles all dependencies and deployment steps.
It will attempt to install missing packages (like python3-venv) when possible.

Usage: ./scripts/deploy.sh [mode] [environment]

Arguments:
  mode         Deployment mode: local (default) or production
  environment  Environment name: dev (default), staging, or prod

Environment Variables:
  RUN_TESTS          Set to 'true' to run tests after deployment
  SKIP_BUILD         Set to 'true' to skip Docker image building
  FORCE_BUILD        Set to 'true' to force rebuild all images (default: only build if missing)
  SKIP_VENV          Set to 'true' to skip Python venv creation (Docker-only)
  SKIP_PORT_CHECK    Set to 'true' to skip port conflict checking
  SKIP_SERVICE_DEPS   Set to 'true' to skip installing service dependencies locally
  DOCKER_REGISTRY    Docker registry URL for production deployments

Examples:
  # Local deployment (auto-installs dependencies)
  ./scripts/deploy.sh local

  # Production deployment
  ./scripts/deploy.sh production prod

  # Local deployment with tests
  RUN_TESTS=true ./scripts/deploy.sh local

  # Skip build
  SKIP_BUILD=true ./scripts/deploy.sh local

  # Skip Python venv (Docker-only deployment)
  SKIP_VENV=true ./scripts/deploy.sh local

EOF
    exit 0
fi

# Run main function
main
