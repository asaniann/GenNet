# GenNet Cloud Platform - Architecture

## System Overview

GenNet is a cloud-native microservices platform for Gene Regulatory Network analysis.

## Architecture Components

### Core Services

1. **API Gateway** (Kong)
   - Request routing
   - Authentication/authorization
   - Rate limiting
   - CORS handling

2. **Auth Service**
   - User authentication (JWT)
   - User registration
   - Session management
   - RBAC

3. **GRN Service**
   - Network CRUD operations
   - Graph storage (Neo4j)
   - Network validation
   - Import/export

4. **Workflow Service**
   - Workflow orchestration
   - Job queuing
   - Status tracking
   - Result management

### Analysis Services

5. **Qualitative Service**
   - CTL formula verification
   - K-parameter generation (SMBioNet)
   - State graph generation
   - Parameter filtering

6. **Hybrid Service**
   - Time delay computation (HyTech)
   - Hybrid automata modeling
   - Trajectory analysis

7. **ML Service**
   - GRN inference (ARACNE, GENIE3, GRNBoost2)
   - Parameter prediction (GNNs)
   - Anomaly detection
   - Disease prediction

### Supporting Services

8. **Collaboration Service**
   - Real-time WebSocket communication
   - Presence tracking
   - Live collaboration

9. **Metadata Service**
   - Data catalog
   - Metadata management

10. **GraphQL Service**
    - GraphQL API
    - Flexible querying

11. **HPC Orchestrator**
    - Kubernetes job management
    - Batch processing
    - GPU scheduling

## Data Flow

1. User creates/imports GRN via web UI
2. Network stored in Neo4j (graph) and PostgreSQL (metadata)
3. User initiates workflow (qualitative/hybrid/ML)
4. Workflow service orchestrates analysis
5. Analysis services execute on HPC cluster
6. Results stored in S3 and metadata in PostgreSQL
7. Results displayed in web UI

## Technology Stack

- **Languages**: Python 3.11+, Go 1.21+, TypeScript
- **Frameworks**: FastAPI, Next.js 14, React
- **Databases**: PostgreSQL, Neo4j, Redis, InfluxDB
- **Cloud**: AWS (EKS, RDS, Neptune, S3, ElastiCache)
- **Container**: Docker, Kubernetes
- **ML**: PyTorch, TensorFlow, scikit-learn

