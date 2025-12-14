# Deployment Scripts

This directory contains deployment and utility scripts for the GenNet platform.

## Scripts

### `deploy.sh` - Main Deployment Script

Unified deployment script that handles both local and production deployments with automatic dependency management and error handling.

**Usage:**
```bash
./scripts/deploy.sh [mode] [environment]
```

**Examples:**
```bash
# Local deployment
./scripts/deploy.sh local

# Production deployment
./scripts/deploy.sh production prod

# With tests
RUN_TESTS=true ./scripts/deploy.sh local

# Skip Docker build
SKIP_BUILD=true ./scripts/deploy.sh local
```

**Features:**
- ✅ Automatic prerequisite checking
- ✅ Dependency installation (Python, Node.js)
- ✅ Docker image building
- ✅ Service deployment (Docker Compose or Kubernetes)
- ✅ Health checks and validation
- ✅ Error handling and logging
- ✅ Support for local and production modes

### `undeploy.sh` - Cleanup Script

Removes deployed services and optionally destroys infrastructure.

**Usage:**
```bash
./scripts/undeploy.sh [mode]
```

**Examples:**
```bash
# Remove local services
./scripts/undeploy.sh local

# Remove production deployment
./scripts/undeploy.sh production
```

### `validate_setup.sh` - Setup Validation

Validates that all prerequisites and dependencies are properly installed.

**Usage:**
```bash
./scripts/validate_setup.sh
```

### `run_tests.sh` - Test Runner

Runs the complete test suite with different options.

**Usage:**
```bash
# Run all tests
./scripts/run_tests.sh

# Run integration tests
RUN_INTEGRATION=true ./scripts/run_tests.sh

# Run E2E tests
RUN_E2E=true ./scripts/run_tests.sh
```

## Environment Variables

### Deployment Script Variables

- `RUN_TESTS`: Set to `true` to run tests after deployment
- `SKIP_BUILD`: Set to `true` to skip Docker image building
- `DOCKER_REGISTRY`: Docker registry URL for production deployments

### Service Configuration

Service-specific environment variables should be set in:
- `docker-compose.yml` (for local)
- Kubernetes ConfigMaps/Secrets (for production)

## Error Handling

All scripts include comprehensive error handling:
- ✅ Pre-flight checks
- ✅ Dependency validation
- ✅ Graceful error messages
- ✅ Exit codes for automation
- ✅ Cleanup on failure

## Logging

Scripts provide colored, structured logging:
- 🔵 INFO - Informational messages
- 🟢 SUCCESS - Successful operations
- 🟡 WARNING - Warnings that don't stop execution
- 🔴 ERROR - Errors that stop execution

## Best Practices

1. **Always validate setup first:**
   ```bash
   ./scripts/validate_setup.sh
   ```

2. **Review configuration before production:**
   ```bash
   # Review terraform.tfvars
   cat infrastructure/terraform/terraform.tfvars
   
   # Review Kubernetes manifests
   kubectl diff -f infrastructure/kubernetes/
   ```

3. **Test locally before production:**
   ```bash
   ./scripts/deploy.sh local
   # Test services
   ./scripts/undeploy.sh local
   ```

4. **Use version control:**
   - Never commit `terraform.tfvars` with real credentials
   - Use environment variables or secrets management
   - Track changes to infrastructure code

## Troubleshooting

If scripts fail:

1. Check prerequisites: `./scripts/validate_setup.sh`
2. Review error messages (they include suggestions)
3. Check service logs: `docker-compose logs` or `kubectl logs`
4. Verify network connectivity and ports
5. Ensure sufficient resources (disk space, memory)

For detailed troubleshooting, see [DEPLOYMENT_GUIDE.md](../docs/DEPLOYMENT_GUIDE.md).

