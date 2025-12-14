# GenNet Cloud Platform

A cloud-native platform for multi-scale Gene Regulatory Network (GRN) analysis, incorporating modern AI/ML, high-performance computing, and collaborative science capabilities.

## 🚀 Quick Start

### One-Command Deployment

```bash
# Local deployment (development)
./scripts/deploy.sh local

# Production deployment
./scripts/deploy.sh production
```

The deployment script automatically:
- ✅ Checks prerequisites
- ✅ Installs all dependencies
- ✅ Builds Docker images
- ✅ Starts all services
- ✅ Validates deployment

### Manual Setup (Alternative)

```bash
# Validate setup
./scripts/validate_setup.sh

# Start local development environment
make dev-up

# Run tests
make test
```

## 📋 Overview

GenNet Cloud Platform is an advanced, cloud-native evolution of the legacy GenNet tool, providing:

- **Multi-Scale GRN Analysis**: From single-cell to tissue-level analysis
- **AI/ML Integration**: Automated GRN inference, parameter prediction, and pattern recognition
- **High-Performance Computing**: Kubernetes-based orchestration with GPU support
- **Collaborative Science**: Real-time collaboration, version control, and shared workspaces
- **Modern Architecture**: Microservices-based, scalable, and cloud-native

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions
- [API Documentation](docs/API.md) - REST API reference
- [Testing Guide](docs/TESTING.md) - Test suite documentation
- [Completion Summary](docs/COMPLETION_SUMMARY.md) - Implementation status

## 🏗️ Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

### Core Services
- **API Gateway**: Kong-based routing and authentication
- **Auth Service**: JWT-based authentication and RBAC
- **GRN Service**: Network management with Neo4j graph storage
- **Workflow Service**: Orchestration of analysis pipelines
- **Collaboration Service**: Real-time WebSocket-based collaboration

### Analysis Services
- **Qualitative Service**: SMBioNet integration for CTL verification
- **Hybrid Service**: HyTech integration for time delay computation
- **ML Service**: GRN inference (ARACNE, GENIE3, GRNBoost2), parameter prediction

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, Go 1.21+, FastAPI, gRPC
- **Frontend**: Next.js 14+, TypeScript, React Flow/Cytoscape.js
- **Infrastructure**: AWS (EKS, RDS, Neptune, S3, ElastiCache), Kubernetes, Terraform
- **Databases**: PostgreSQL, Neo4j/Neptune, Redis, InfluxDB
- **ML/AI**: PyTorch, TensorFlow, MLflow, scikit-learn

## 🧪 Testing

```bash
# Run all tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# With coverage
make test-coverage
```

See [TESTING.md](docs/TESTING.md) for detailed testing documentation.

## 📦 Project Structure

```
gennet-platform/
├── infrastructure/          # Terraform, Kubernetes manifests
├── services/                # Microservices
│   ├── api-gateway/
│   ├── auth-service/
│   ├── grn-service/
│   ├── workflow-service/
│   ├── qualitative-service/
│   ├── hybrid-service/
│   ├── ml-service/
│   ├── collaboration-service/
│   ├── metadata-service/
│   ├── graphql-service/
│   └── hpc-orchestrator/
├── frontend/                # Next.js web application
├── libraries/               # Python SDK
├── tools/                   # Data ingestion, migration tools
├── tests/                   # Integration and E2E tests
└── docs/                    # Documentation
```

## 🔐 Security

- JWT-based authentication
- Password hashing (bcrypt)
- Encryption utilities
- Audit logging
- Input validation
- CORS configuration

## 📈 Features

### GRN Management
- Create, edit, and visualize GRN networks
- Import from multiple formats (SBML, BioPAX, CSV, JSON)
- Network validation and consistency checking
- Graph-based storage with Neo4j

### Analysis Workflows
- **Qualitative Modeling**: CTL verification, K-parameter generation, state graph analysis
- **Hybrid Modeling**: Time delay computation, trajectory analysis
- **ML/AI Analysis**: GRN inference, parameter prediction, anomaly detection, disease prediction

### Collaboration
- Real-time collaborative editing
- Presence tracking
- Version control
- Shared workspaces

### HPC Integration
- Kubernetes-based job orchestration
- GPU cluster support
- Distributed computing (Ray, Dask)
- Batch processing

## 🚢 Deployment

### Quick Deploy

**Docker-only (Recommended - no Python venv needed):**
```bash
SKIP_VENV=true ./scripts/deploy.sh local
```

**Full local deployment (requires python3-venv):**
```bash
./scripts/deploy.sh local
```

**Production deployment:**
```bash
./scripts/deploy.sh production
```

> **Note:** If you encounter `python3-venv` errors, either install it (`sudo apt install python3.12-venv`) or use `SKIP_VENV=true` for Docker-only deployment.

The deployment script automatically handles:
- Prerequisite checking
- Dependency installation
- Docker image building
- Service startup
- Health validation
- Error handling

See [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) for quick reference or [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for detailed instructions.

### Local Development

```bash
# Start services with Docker Compose
make dev-up

# Run individual services
cd services/auth-service
uvicorn main:app --reload
```

### Production

```bash
# Deploy infrastructure
cd infrastructure/terraform
terraform apply

# Deploy services to Kubernetes
kubectl apply -f infrastructure/kubernetes/
```

## 📖 API Usage

### Python SDK

```python
from gennet import GenNetClient

client = GenNetClient(base_url="https://api.gennet.com", api_key="your-key")

# List networks
networks = client.list_networks()

# Create workflow
workflow = client.create_workflow(
    name="My Analysis",
    workflow_type="qualitative",
    network_id="network-123"
)
```

### REST API

See [API.md](docs/API.md) for complete API documentation.

### Postman Collection

Import `docs/API.postman_collection.json` into Postman for interactive API testing.

## 🤝 Contributing

[Contributing guidelines to be added]

## 📄 License

[To be determined]

## ✅ Status

**Status**: ✅ **COMPLETE** - All planned features implemented and tested.

See [COMPLETION_SUMMARY.md](docs/COMPLETION_SUMMARY.md) for detailed implementation status.

---

For questions or support, please refer to the documentation or open an issue.
