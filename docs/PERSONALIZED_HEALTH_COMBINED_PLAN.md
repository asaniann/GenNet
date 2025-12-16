# Personalized Health Platform - Unified Implementation Plan
## Combined GRN and Non-GRN Approaches

## Executive Summary

This document presents a **unified, enhanced implementation plan** for building a comprehensive personalized health prediction platform that seamlessly integrates **both Gene Regulatory Network (GRN) modeling and direct non-GRN analysis methods**. The system leverages the complementary strengths of both approaches to provide the most accurate, comprehensive, and actionable personalized health insights.

### Key Innovation: Hybrid Intelligence System

The platform uses an **intelligent routing and ensemble system** that:
- **Automatically selects** the best analysis method(s) based on available data
- **Combines predictions** from multiple approaches for enhanced accuracy
- **Provides fallback mechanisms** when certain data types are unavailable
- **Leverages GRN insights** when expression data is available
- **Uses direct methods** (PRS, signatures) when GRN construction isn't feasible

---

## Table of Contents

1. [Unified Project Overview](#unified-project-overview)
2. [Enhanced System Architecture](#enhanced-system-architecture)
3. [Hybrid Analysis Framework](#hybrid-analysis-framework)
4. [Core Components (Unified)](#core-components-unified)
5. [Implementation Phases](#implementation-phases)
6. [Technical Specifications](#technical-specifications)
7. [Unified Data Models](#unified-data-models)
8. [Enhanced API Design](#enhanced-api-design)
9. [Intelligent Routing System](#intelligent-routing-system)
10. [Security & Privacy](#security--privacy)
11. [Testing Strategy](#testing-strategy)
12. [Deployment Plan](#deployment-plan)
13. [Timeline & Milestones](#timeline--milestones)
14. [Success Metrics](#success-metrics)

---

## 1. Unified Project Overview

### 1.1 Vision

Build the **most comprehensive personalized health platform** that combines:
- **Network-based insights** (GRN modeling) for understanding regulatory mechanisms
- **Direct genomic analysis** (PRS, variants) for rapid risk assessment
- **Expression signatures** for disease classification and prognosis
- **Multi-omics integration** for holistic health profiling
- **Clinical data fusion** for evidence-based recommendations
- **Pharmacogenomics** for personalized medicine

### 1.2 Core Objectives

1. **Comprehensive Analysis**: Support both GRN and non-GRN approaches
2. **Intelligent Routing**: Automatically select optimal analysis methods
3. **Ensemble Predictions**: Combine multiple methods for maximum accuracy
4. **Flexible Data Requirements**: Work with varying data availability
5. **Scalable Architecture**: Support 10,000+ concurrent users
6. **Clinical Integration**: Seamless EHR and clinical decision support
7. **Regulatory Compliance**: Full HIPAA/GDPR compliance

### 1.3 Enhanced Use Cases

#### Use Case 1: Comprehensive Health Assessment
**Scenario**: Patient has genomic (VCF), expression (RNA-seq), and clinical data

**Analysis Flow**:
1. **Non-GRN Path**: Calculate PRS, score expression signatures, analyze clinical data
2. **GRN Path**: Construct personalized GRN, analyze network perturbations
3. **Integration**: Multi-omics fusion combines all data types
4. **Ensemble**: Weighted combination of all predictions
5. **Output**: Comprehensive health report with multiple evidence sources

#### Use Case 2: Limited Data Scenario
**Scenario**: Patient only has genomic data (VCF file)

**Analysis Flow**:
1. **Non-GRN Path**: Calculate PRS, annotate variants, assess pathogenicity
2. **GRN Path**: Skip (insufficient data)
3. **Integration**: Use population reference data for context
4. **Ensemble**: PRS-based predictions with clinical guidelines
5. **Output**: Genomic risk assessment with actionable recommendations

#### Use Case 3: Expression-Only Analysis
**Scenario**: Patient has expression data but no genomic variants

**Analysis Flow**:
1. **Non-GRN Path**: Score expression signatures, identify biomarkers
2. **GRN Path**: Construct GRN from expression data, analyze perturbations
3. **Integration**: Combine signature scores with network insights
4. **Ensemble**: Expression + GRN predictions
5. **Output**: Expression-based health profile with network context

#### Use Case 4: Longitudinal Monitoring
**Scenario**: Patient with multiple time points of data

**Analysis Flow**:
1. **Non-GRN Path**: Track PRS changes, expression signature trends
2. **GRN Path**: Compare GRN changes over time, detect network shifts
3. **Integration**: Multi-temporal analysis across all omics
4. **Ensemble**: Temporal ensemble with change detection
5. **Output**: Health trend report with progression indicators

### 1.4 Success Criteria

- **Prediction Accuracy**: >90% (ensemble) vs >85% (individual methods)
- **Coverage**: Support 95%+ of patients with at least one analysis method
- **Performance**: <30s for PRS, <5s for signatures, <60s for GRN inference
- **Scalability**: 10,000+ concurrent users
- **Compliance**: Full HIPAA/GDPR compliance
- **Method Selection**: >95% accuracy in optimal method selection

---

## 2. Enhanced System Architecture

### 2.1 Unified Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                            │
│  - Unified Patient Dashboard                                     │
│  - Health Reports (GRN + Non-GRN)                               │
│  - Interactive Network Visualizations                           │
│  - Multi-omics Data Explorer                                    │
│  - Method Comparison Views                                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                  API Gateway (Kong)                               │
│  - Authentication & Authorization                                 │
│  - Intelligent Request Routing                                    │
│  - Rate Limiting & Caching                                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│ Analysis     │ │ Patient     │ │ Health     │
│ Router       │ │ Data        │ │ Service    │
│ Service      │ │ Service     │ │            │
│ (NEW)        │ │             │ │            │
└───────┬──────┘ └─────┬──────┘ └─────┬──────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
┌───▼────┐      ┌──────▼──────┐    ┌─────▼──────┐
│ Non-GRN│      │   GRN        │    │ Ensemble   │
│ Branch │      │   Branch     │    │ Service    │
└───┬────┘      └──────┬───────┘    └─────┬──────┘
    │                  │                  │
    │                  │                  │
┌───▼────┐      ┌──────▼──────┐    ┌─────▼──────┐
│Genomic │      │GRN Service  │    │Prediction   │
│Analysis│      │(Enhanced)    │    │Aggregator   │
│Service │      │             │    │             │
└───┬────┘      └──────┬──────┘    └─────┬──────┘
    │                  │                  │
┌───▼────┐      ┌──────▼──────┐    ┌─────▼──────┐
│Express │      │ML Service    │    │Report      │
│Analysis│      │(GRN Inference)│   │Generator   │
│Service │      │             │    │             │
└───┬────┘      └──────┬──────┘    └─────┬──────┘
    │                  │                  │
┌───▼────┐      ┌──────▼──────┐    ┌─────▼──────┐
│Multi-  │      │Workflow     │    │Recommen-   │
│Omics   │      │Service      │    │dation      │
│Service │      │             │    │Engine      │
└───┬────┘      └──────┬──────┘    └────────────┘
    │                  │
┌───▼────┐      ┌──────▼──────┐
│Clinical│      │Qualitative   │
│Data    │      │Service      │
│Service │      │             │
└────────┘      └─────────────┘
```

### 2.2 Key New Services

#### 1. Analysis Router Service (NEW - Core Innovation)
**Purpose**: Intelligent routing and method selection

**Responsibilities**:
- Analyze available patient data
- Determine optimal analysis methods
- Route requests to appropriate services
- Coordinate parallel analysis execution
- Manage fallback strategies

**Key Features**:
- Data availability assessment
- Method feasibility checking
- Resource optimization
- Quality-based method selection

**Location**: `services/analysis-router-service/`

#### 2. Ensemble Service (NEW - Enhanced)
**Purpose**: Combine predictions from multiple methods

**Responsibilities**:
- Weighted ensemble predictions
- Confidence calibration
- Method-specific weighting
- Uncertainty quantification
- Evidence aggregation

**Key Features**:
- Adaptive weighting based on data quality
- Method confidence integration
- Consensus building
- Disagreement detection

**Location**: `services/ensemble-service/`

#### 3. Enhanced Existing Services

**GRN Service** (Enhanced):
- Patient-specific GRN construction
- Network comparison tools
- Perturbation analysis
- Integration with non-GRN methods

**ML Service** (Enhanced):
- GRN inference (ARACNE, GENIE3, GRNBoost2)
- Non-GRN models (PRS, signatures, classifiers)
- Hybrid model training
- Transfer learning

**Health Service** (Enhanced):
- Unified health reports
- Method comparison views
- Evidence integration
- Recommendation engine

### 2.3 Data Flow (Unified)

```
Patient Data Upload
        │
        ├─→ Data Assessment (Router)
        │
        ├─→ [Non-GRN Branch]
        │   ├─→ Genomic Analysis (PRS, Variants)
        │   ├─→ Expression Analysis (Signatures)
        │   ├─→ Clinical Data Integration
        │   └─→ Multi-Omics Fusion
        │
        ├─→ [GRN Branch] (if expression data available)
        │   ├─→ GRN Construction
        │   ├─→ Network Analysis
        │   └─→ Perturbation Detection
        │
        └─→ Ensemble Service
            ├─→ Prediction Aggregation
            ├─→ Confidence Calibration
            └─→ Evidence Integration
                │
                └─→ Health Service
                    ├─→ Report Generation
                    ├─→ Recommendations
                    └─→ Visualization
```

---

## 3. Hybrid Analysis Framework

### 3.1 Intelligent Method Selection

The system uses a **decision tree** to select optimal analysis methods:

```python
class AnalysisRouter:
    def select_methods(
        self,
        patient_data: PatientDataProfile
    ) -> AnalysisPlan:
        """
        Intelligently select analysis methods based on available data
        """
        plan = AnalysisPlan()
        
        # Check genomic data availability
        if patient_data.has_genomic_data():
            plan.add_method("prs")
            plan.add_method("variant_annotation")
            plan.add_method("pharmacogenomics")
        
        # Check expression data availability
        if patient_data.has_expression_data():
            plan.add_method("expression_signatures")
            plan.add_method("biomarker_identification")
            
            # GRN construction if sufficient expression data
            if patient_data.expression_data.is_sufficient_for_grn():
                plan.add_method("grn_construction")
                plan.add_method("network_perturbation")
        
        # Check clinical data availability
        if patient_data.has_clinical_data():
            plan.add_method("clinical_integration")
            plan.add_method("clinical_decision_support")
        
        # Check multi-omics availability
        if patient_data.has_multiple_omics():
            plan.add_method("multi_omics_fusion")
            plan.add_method("integrated_analysis")
        
        # Determine ensemble strategy
        plan.set_ensemble_strategy(
            self._determine_ensemble_strategy(plan)
        )
        
        return plan
```

### 3.2 Method Feasibility Matrix

| Data Available | Non-GRN Methods | GRN Methods | Best Approach |
|----------------|----------------|------------|---------------|
| Genomic only | PRS, Variants | None | Non-GRN |
| Expression only | Signatures, Biomarkers | GRN Construction | Both (weighted) |
| Genomic + Expression | PRS, Signatures | GRN Construction | Ensemble (both) |
| Genomic + Expression + Clinical | All Non-GRN | GRN + Clinical | Full Ensemble |
| Multi-Omics | All Non-GRN | GRN + Multi-Omics | Advanced Ensemble |

### 3.3 Ensemble Strategies

#### Strategy 1: Weighted Voting
- Weight predictions by method confidence
- Adjust weights based on data quality
- Use validation performance for base weights

#### Strategy 2: Stacking
- Train meta-learner on method predictions
- Learn optimal combination
- Adapt to patient-specific patterns

#### Strategy 3: Bayesian Model Averaging
- Probabilistic combination
- Uncertainty quantification
- Credible intervals

#### Strategy 4: Adaptive Ensemble
- Select ensemble method based on:
  - Number of available methods
  - Agreement between methods
  - Data quality scores
  - Historical performance

### 3.4 Fallback Mechanisms

**Scenario 1**: GRN construction fails
- Fallback to expression signatures
- Use reference GRN with patient adjustments
- Report reduced confidence

**Scenario 2**: Insufficient expression data for GRN
- Use PRS and variant analysis
- Leverage population reference data
- Provide genomic-only predictions

**Scenario 3**: Missing clinical data
- Use genomic/expression predictions
- Apply population-based clinical priors
- Flag limited clinical context

---

## 4. Core Components (Unified)

### 4.1 Genomic Analysis (Non-GRN)

**Components**:
- **Variant Calling & Annotation**: Parse VCF, annotate variants
- **PRS Calculator**: Calculate polygenic risk scores
- **Pathogenicity Predictor**: Assess variant impact
- **Population Frequency Analyzer**: Compare to reference populations

**Location**: `services/genomic-analysis-service/`

**Key Files**:
- `variant_annotator.py`
- `prs_calculator.py`
- `pathogenicity_predictor.py`
- `population_analyzer.py`

### 4.2 Expression Analysis (Non-GRN)

**Components**:
- **Signature Scorer**: Score disease/treatment signatures
- **Biomarker Identifier**: Identify diagnostic biomarkers
- **Disease Classifier**: Expression-based classification
- **Pathway Scorer**: Pathway activity scoring

**Location**: `services/expression-analysis-service/`

**Key Files**:
- `signature_scorer.py`
- `biomarker_finder.py`
- `disease_classifier.py`
- `pathway_scorer.py`

### 4.3 GRN Analysis (GRN-Based)

**Components**:
- **Personalized GRN Builder**: Construct patient-specific GRNs
- **Network Perturbation Analyzer**: Detect network disruptions
- **Pathway Activity Scorer**: Score pathway activities from GRN
- **Drug Target Identifier**: Identify drug targets in GRN

**Location**: `services/grn-service/` (enhanced)

**Key Files**:
- `personalized_grn_builder.py`
- `perturbation_analyzer.py`
- `pathway_analyzer.py`
- `drug_target_finder.py`

### 4.4 Multi-Omics Integration

**Components**:
- **Data Fusion Engine**: Fuse multiple omics types
- **Cross-Omics Correlator**: Find cross-omics relationships
- **Integrated Predictor**: Multi-omics prediction models
- **Biomarker Integrator**: Integrate biomarkers across omics

**Location**: `services/multi-omics-service/`

**Key Files**:
- `data_fusion.py`
- `correlation_analyzer.py`
- `integrated_predictor.py`
- `biomarker_integrator.py`

### 4.5 Clinical Integration

**Components**:
- **FHIR Client**: Integrate with EHR systems
- **Clinical Decision Support**: Evidence-based recommendations
- **Lab Interpreter**: Interpret lab results
- **Risk Stratifier**: Clinical risk stratification

**Location**: `services/clinical-data-service/`

**Key Files**:
- `fhir_client.py`
- `decision_support.py`
- `lab_interpreter.py`
- `risk_stratifier.py`

### 4.6 Pharmacogenomics

**Components**:
- **Drug-Gene Interaction DB**: Database of interactions
- **Response Predictor**: Predict drug response
- **Dosing Calculator**: Calculate optimal dosing
- **Interaction Analyzer**: Analyze drug-drug interactions

**Location**: `services/pharmacogenomics-service/`

**Key Files**:
- `drug_gene_db.py`
- `response_predictor.py`
- `dosing_calculator.py`
- `interaction_analyzer.py`

### 4.7 Analysis Router (NEW)

**Components**:
- **Data Assessor**: Assess available data
- **Method Selector**: Select optimal methods
- **Route Manager**: Manage request routing
- **Fallback Handler**: Handle fallback scenarios

**Location**: `services/analysis-router-service/`

**Key Files**:
- `data_assessor.py`
- `method_selector.py`
- `route_manager.py`
- `fallback_handler.py`

### 4.8 Ensemble Service (NEW)

**Components**:
- **Prediction Aggregator**: Aggregate predictions
- **Weight Calculator**: Calculate method weights
- **Confidence Calibrator**: Calibrate confidence scores
- **Evidence Integrator**: Integrate evidence from all methods

**Location**: `services/ensemble-service/`

**Key Files**:
- `prediction_aggregator.py`
- `weight_calculator.py`
- `confidence_calibrator.py`
- `evidence_integrator.py`

---

## 5. Implementation Phases

### Phase 1: Foundation & Core Services (Weeks 1-8)

**Goals**: Build foundation and core analysis services

**Tasks**:
1. **Patient Data Service**
   - Unified patient data model
   - Data ingestion pipeline
   - Privacy controls

2. **Genomic Analysis Service** (Non-GRN)
   - VCF parsing
   - Variant annotation
   - PRS calculation

3. **Expression Analysis Service** (Non-GRN)
   - Expression normalization
   - Signature scoring
   - Biomarker identification

4. **GRN Service Enhancement** (GRN)
   - Patient-specific GRN construction
   - Network analysis tools
   - Perturbation detection

5. **Basic Infrastructure**
   - Database setup
   - S3 storage
   - Redis caching

**Deliverables**:
- Patient Data Service
- Genomic Analysis Service
- Expression Analysis Service
- Enhanced GRN Service
- Basic APIs

### Phase 2: Multi-Omics & Clinical Integration (Weeks 9-14)

**Goals**: Add multi-omics and clinical integration

**Tasks**:
1. **Multi-Omics Service**
   - Data fusion algorithms
   - Cross-omics analysis
   - Integrated models

2. **Clinical Data Service**
   - FHIR integration
   - Clinical decision support
   - Lab interpretation

3. **Pharmacogenomics Service**
   - Drug-gene interactions
   - Response prediction
   - Dosing recommendations

**Deliverables**:
- Multi-Omics Service
- Clinical Data Service
- Pharmacogenomics Service
- Integration APIs

### Phase 3: Analysis Router & Intelligent Routing (Weeks 15-18)

**Goals**: Build intelligent routing system

**Tasks**:
1. **Analysis Router Service**
   - Data assessment
   - Method selection
   - Request routing
   - Fallback handling

2. **Method Feasibility Engine**
   - Data quality assessment
   - Method feasibility checking
   - Resource optimization

3. **Integration Testing**
   - End-to-end workflows
   - Method selection accuracy
   - Fallback scenarios

**Deliverables**:
- Analysis Router Service
- Intelligent routing working
- Method selection validated

### Phase 4: Ensemble Service & Prediction Aggregation (Weeks 19-22)

**Goals**: Build ensemble prediction system

**Tasks**:
1. **Ensemble Service**
   - Prediction aggregation
   - Weight calculation
   - Confidence calibration
   - Evidence integration

2. **Ensemble Strategies**
   - Weighted voting
   - Stacking
   - Bayesian averaging
   - Adaptive ensemble

3. **Validation**
   - Ensemble performance testing
   - Method weight optimization
   - Confidence calibration

**Deliverables**:
- Ensemble Service
- Multiple ensemble strategies
- Validated ensemble performance

### Phase 5: Health Service & Reporting (Weeks 23-26)

**Goals**: Build unified health service and reporting

**Tasks**:
1. **Health Service Enhancement**
   - Unified health reports
   - Method comparison views
   - Evidence integration
   - Recommendation engine

2. **Report Generation**
   - PDF report generation
   - Interactive visualizations
   - Method-specific sections
   - Evidence summaries

3. **Visualization**
   - Network visualizations (GRN)
   - Genomic visualizations (variants, PRS)
   - Expression visualizations (signatures)
   - Multi-omics dashboards

**Deliverables**:
- Enhanced Health Service
- Unified report generation
- Comprehensive visualizations

### Phase 6: Frontend & User Experience (Weeks 27-30)

**Goals**: Build unified frontend

**Tasks**:
1. **Unified Dashboard**
   - Patient overview
   - Method comparison
   - Evidence visualization
   - Health trends

2. **Data Upload Interface**
   - Multi-format support
   - Data validation
   - Processing status
   - Result display

3. **Interactive Features**
   - Network exploration (GRN)
   - Variant exploration (genomic)
   - Signature exploration (expression)
   - Multi-omics explorer

**Deliverables**:
- Complete frontend
- Unified user experience
- Interactive visualizations

### Phase 7: Testing & Optimization (Weeks 31-34)

**Goals**: Comprehensive testing and optimization

**Tasks**:
1. **Testing**
   - Unit tests (>85% coverage)
   - Integration tests
   - End-to-end tests
   - Performance tests

2. **Optimization**
   - Query optimization
   - Caching strategies
   - API response times
   - Resource usage

3. **Clinical Validation**
   - Model validation
   - Accuracy testing
   - Bias assessment
   - Reproducibility

**Deliverables**:
- Comprehensive test suite
- Optimized performance
- Clinical validation results

### Phase 8: Security, Compliance & Deployment (Weeks 35-36)

**Goals**: Security hardening and production deployment

**Tasks**:
1. **Security**
   - Security audit
   - Penetration testing
   - Vulnerability scanning
   - Access control review

2. **Compliance**
   - HIPAA compliance review
   - GDPR compliance review
   - Audit logging
   - Data retention policies

3. **Deployment**
   - Production infrastructure
   - Service deployment
   - Monitoring setup
   - Documentation

**Deliverables**:
- Security-hardened system
- Compliance verified
- Production deployment
- Complete documentation

---

## 6. Technical Specifications

### 6.1 Technology Stack

#### Backend Services
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Databases**:
  - PostgreSQL 15+ (patient metadata, variants, clinical data)
  - Neo4j 5+ (GRN networks)
  - Redis 7+ (caching, sessions)
  - InfluxDB 2+ (time-series data)
- **Storage**: AWS S3 (genomic files, expression data)
- **Message Queue**: RabbitMQ or AWS SQS
- **ML Framework**: PyTorch, TensorFlow, scikit-learn, XGBoost

#### Genomics Libraries
- **VCF Parsing**: cyvcf2, pysam
- **Variant Annotation**: VEP, SnpEff
- **Genomics**: pandas, numpy, scipy

#### GRN Libraries
- **Network Analysis**: NetworkX, igraph
- **GRN Inference**: Custom implementations (ARACNE, GENIE3, GRNBoost2)
- **Graph ML**: PyTorch Geometric, DGL

#### Clinical Libraries
- **FHIR**: fhir.resources, fhirclient
- **HL7**: hl7

#### Frontend
- **Framework**: Next.js 14+
- **Language**: TypeScript
- **Visualization**: 
  - D3.js (general)
  - Cytoscape.js (GRN networks)
  - Plotly (charts)
  - Recharts (dashboards)
- **UI Components**: Tailwind CSS, shadcn/ui

#### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **Cloud**: AWS (EKS, RDS, Neptune, S3, ElastiCache)
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack

### 6.2 Performance Requirements

- **PRS Calculation**: <30 seconds
- **Expression Analysis**: <5 seconds
- **GRN Inference**: <60 seconds
- **Multi-Omics Integration**: <10 seconds
- **Ensemble Prediction**: <2 seconds
- **API Response Time**: <500ms (p95) for simple queries, <5s for predictions
- **Concurrent Users**: 10,000+
- **Data Processing**: 1000+ patients/hour

### 6.3 Scalability Considerations

- **Horizontal Scaling**: All services stateless
- **Database Sharding**: Patient data sharded by patient_id
- **Caching**: Multi-layer (Redis, CDN)
- **Async Processing**: Background jobs for heavy computations
- **Load Balancing**: Kubernetes service mesh (Istio)

---

## 7. Unified Data Models

### 7.1 Patient Model (Enhanced)

```python
class Patient(Base):
    __tablename__ = "patients"
    
    id: str = Column(String, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("users.id"))
    anonymized_id: str = Column(String, unique=True, index=True)
    
    # Demographics
    age_range: str = Column(String)
    gender: Optional[str] = Column(String)
    ethnicity: Optional[str] = Column(String)
    
    # Data availability flags
    has_genomic_data: bool = Column(Boolean, default=False)
    has_expression_data: bool = Column(Boolean, default=False)
    has_clinical_data: bool = Column(Boolean, default=False)
    has_multi_omics: bool = Column(Boolean, default=False)
    
    # Metadata
    created_at: datetime = Column(DateTime)
    updated_at: datetime = Column(DateTime)
    consent_given: bool = Column(Boolean)
    
    # Relationships
    genomic_profiles: List["GenomicProfile"]
    expression_profiles: List["ExpressionProfile"]
    grn_networks: List["PatientGRN"]
    clinical_data: List["ClinicalData"]
    health_predictions: List["HealthPrediction"]
```

### 7.2 Analysis Plan Model (NEW)

```python
class AnalysisPlan(Base):
    __tablename__ = "analysis_plans"
    
    id: str = Column(String, primary_key=True)
    patient_id: str = Column(String, ForeignKey("patients.id"))
    
    # Selected methods
    methods: List[str] = Column(JSON)  # ["prs", "expression", "grn", ...]
    ensemble_strategy: str = Column(String)  # "weighted_voting", "stacking", etc.
    
    # Feasibility
    grn_feasible: bool = Column(Boolean)
    grn_feasibility_reason: Optional[str] = Column(String)
    
    # Execution status
    status: str = Column(String)  # "planned", "executing", "completed", "failed"
    started_at: Optional[datetime] = Column(DateTime)
    completed_at: Optional[datetime] = Column(DateTime)
    
    # Results
    prediction_ids: List[str] = Column(JSON)
    ensemble_prediction_id: Optional[str] = Column(String)
```

### 7.3 Unified Prediction Model (Enhanced)

```python
class HealthPrediction(Base):
    __tablename__ = "health_predictions"
    
    id: str = Column(String, primary_key=True)
    patient_id: str = Column(String, ForeignKey("patients.id"))
    analysis_plan_id: str = Column(String, ForeignKey("analysis_plans.id"))
    
    # Prediction details
    prediction_type: str = Column(String)
    disease_code: str = Column(String)
    disease_name: str = Column(String)
    
    # Method information
    method: str = Column(String)  # "prs", "expression", "grn", "multi_omics", "ensemble"
    is_ensemble: bool = Column(Boolean, default=False)
    
    # Scores
    risk_score: float = Column(Float)
    confidence_interval_lower: float = Column(Float)
    confidence_interval_upper: float = Column(Float)
    confidence_level: float = Column(Float)
    
    # Evidence (method-specific)
    genomic_evidence: Optional[Dict] = Column(JSON)
    expression_evidence: Optional[Dict] = Column(JSON)
    grn_evidence: Optional[Dict] = Column(JSON)
    clinical_evidence: Optional[Dict] = Column(JSON)
    multi_omics_evidence: Optional[Dict] = Column(JSON)
    
    # Ensemble information (if ensemble)
    component_predictions: Optional[List[str]] = Column(JSON)  # IDs of component predictions
    method_weights: Optional[Dict[str, float]] = Column(JSON)
    agreement_score: Optional[float] = Column(Float)  # Agreement between methods
    
    # Metadata
    model_version: str = Column(String)
    prediction_date: datetime = Column(DateTime)
```

### 7.4 Ensemble Result Model (NEW)

```python
class EnsemblePrediction(Base):
    __tablename__ = "ensemble_predictions"
    
    id: str = Column(String, primary_key=True)
    analysis_plan_id: str = Column(String, ForeignKey("analysis_plans.id"))
    
    # Ensemble details
    ensemble_strategy: str = Column(String)
    component_prediction_ids: List[str] = Column(JSON)
    
    # Final prediction
    disease_code: str = Column(String)
    disease_name: str = Column(String)
    risk_score: float = Column(Float)
    confidence: float = Column(Float)
    
    # Method contributions
    method_contributions: Dict[str, float] = Column(JSON)
    method_weights: Dict[str, float] = Column(JSON)
    
    # Agreement metrics
    agreement_score: float = Column(Float)
    disagreement_details: Optional[Dict] = Column(JSON)
    
    # Evidence summary
    evidence_summary: Dict = Column(JSON)
    
    # Timestamps
    created_at: datetime = Column(DateTime)
```

---

## 8. Enhanced API Design

### 8.1 Analysis Router API

#### Request Analysis
```http
POST /api/v1/analyze/request
Content-Type: application/json

{
  "patient_id": "patient-123",
  "data_types": ["genomic", "expression", "clinical"],
  "preferences": {
    "prefer_grn": true,
    "require_ensemble": true
  }
}

Response: 200 OK
{
  "analysis_plan_id": "plan-456",
  "selected_methods": [
    "prs",
    "expression_signatures",
    "grn_construction",
    "multi_omics_fusion"
  ],
  "ensemble_strategy": "weighted_voting",
  "grn_feasible": true,
  "estimated_completion": "2024-01-15T10:05:00Z"
}
```

### 8.2 Unified Prediction API

#### Get Comprehensive Predictions
```http
GET /api/v1/health/{patient_id}/predictions/comprehensive
Query: ?disease=ICD10:C50&include_methods=all

Response: 200 OK
{
  "patient_id": "patient-123",
  "disease_code": "ICD10:C50",
  "disease_name": "Breast Cancer",
  
  "ensemble_prediction": {
    "risk_score": 78.5,
    "confidence": 0.92,
    "ensemble_strategy": "weighted_voting",
    "agreement_score": 0.85
  },
  
  "method_predictions": [
    {
      "method": "prs",
      "risk_score": 72.5,
      "confidence": 0.89,
      "weight": 0.25,
      "evidence": {
        "prs_score": 1.25,
        "percentile": 85.3,
        "variant_count": 1200
      }
    },
    {
      "method": "expression",
      "risk_score": 80.0,
      "confidence": 0.93,
      "weight": 0.30,
      "evidence": {
        "signature_score": 0.85,
        "p_value": 0.001,
        "top_genes": ["ESR1", "ERBB2"]
      }
    },
    {
      "method": "grn",
      "risk_score": 75.0,
      "confidence": 0.87,
      "weight": 0.25,
      "evidence": {
        "perturbed_pathways": ["p53_pathway", "cell_cycle"],
        "network_perturbation_score": 0.78
      }
    },
    {
      "method": "multi_omics",
      "risk_score": 76.5,
      "confidence": 0.90,
      "weight": 0.20,
      "evidence": {
        "fusion_score": 0.82,
        "cross_omics_correlations": 0.75
      }
    }
  ],
  
  "evidence_summary": {
    "genomic": "High PRS (85th percentile), pathogenic variants in BRCA1",
    "expression": "Strong disease signature (p<0.001), ERBB2 overexpression",
    "grn": "Perturbed p53 and cell cycle pathways",
    "clinical": "Family history, age 45"
  }
}
```

### 8.3 Method Comparison API

#### Compare Methods
```http
GET /api/v1/health/{patient_id}/predictions/compare
Query: ?disease=ICD10:C50

Response: 200 OK
{
  "comparison": {
    "disease_code": "ICD10:C50",
    "methods": [
      {
        "method": "prs",
        "available": true,
        "risk_score": 72.5,
        "confidence": 0.89,
        "data_quality": 0.95
      },
      {
        "method": "expression",
        "available": true,
        "risk_score": 80.0,
        "confidence": 0.93,
        "data_quality": 0.92
      },
      {
        "method": "grn",
        "available": true,
        "risk_score": 75.0,
        "confidence": 0.87,
        "data_quality": 0.88
      }
    ],
    "agreement": {
      "average_agreement": 0.85,
      "disagreements": []
    }
  }
}
```

---

## 9. Intelligent Routing System

### 9.1 Routing Logic

```python
class IntelligentRouter:
    def route_analysis(
        self,
        patient_id: str,
        data_availability: DataAvailability
    ) -> AnalysisRoute:
        """
        Intelligently route analysis based on data availability
        """
        route = AnalysisRoute()
        
        # Always available: Genomic analysis (if genomic data)
        if data_availability.has_genomic:
            route.add_path("genomic_analysis", priority=1)
        
        # Expression analysis (if expression data)
        if data_availability.has_expression:
            route.add_path("expression_analysis", priority=1)
            
            # GRN construction if sufficient expression data
            if data_availability.expression_quality >= 0.8:
                route.add_path("grn_construction", priority=2)
        
        # Clinical integration (if clinical data)
        if data_availability.has_clinical:
            route.add_path("clinical_integration", priority=1)
        
        # Multi-omics if multiple omics available
        if data_availability.omics_count >= 2:
            route.add_path("multi_omics_fusion", priority=3)
        
        # Ensemble if multiple methods available
        if len(route.paths) >= 2:
            route.add_path("ensemble", priority=4)
        
        return route
```

### 9.2 Quality-Based Selection

- **Data Quality Scores**: Assess quality of each data type
- **Method Feasibility**: Check if methods can run with available data
- **Historical Performance**: Use past performance to weight methods
- **Resource Availability**: Consider computational resources

### 9.3 Fallback Strategies

1. **GRN Construction Fails**: Fallback to expression signatures
2. **Insufficient Expression**: Use PRS and variant analysis
3. **Missing Clinical Data**: Use genomic/expression predictions with population priors
4. **Single Method Available**: Provide method-specific predictions with appropriate confidence

---

## 10. Security & Privacy

### 10.1 Data Security

- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Access Control**: RBAC, JWT authentication
- **Data Isolation**: Multi-tenant isolation
- **Key Management**: AWS KMS

### 10.2 Privacy Protection

- **Anonymization**: Patient IDs anonymized
- **De-identification**: Remove PII from all data
- **Consent Management**: Track and enforce consent
- **Data Minimization**: Store only necessary data

### 10.3 Compliance

- **HIPAA**: Full compliance
- **GDPR**: Right to access, erasure, portability
- **Audit Logging**: Comprehensive audit trails
- **Data Retention**: Configurable retention policies

---

## 11. Testing Strategy

### 11.1 Unit Testing

- **Coverage Target**: >85%
- **Focus**: Business logic, algorithms, data models

### 11.2 Integration Testing

- Service-to-service communication
- Method selection accuracy
- Ensemble prediction correctness
- Fallback scenario handling

### 11.3 Performance Testing

- Load testing (10,000+ users)
- Method execution times
- Ensemble aggregation performance
- API response times

### 11.4 Clinical Validation

- Model validation on independent datasets
- Ensemble vs individual method accuracy
- Bias testing
- Reproducibility

---

## 12. Deployment Plan

### 12.1 Infrastructure

- **AWS EKS**: Kubernetes cluster
- **RDS**: PostgreSQL databases
- **Neptune**: Neo4j-compatible graph database
- **S3**: File storage
- **ElastiCache**: Redis caching
- **VPC**: Network isolation

### 12.2 Deployment Strategy

- **Blue-Green**: Zero-downtime deployments
- **Canary**: Gradual rollouts
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack

---

## 13. Timeline & Milestones

### 13.1 Phase Timeline

| Phase | Duration | Start Week | End Week |
|-------|----------|------------|----------|
| Phase 1: Foundation & Core Services | 8 weeks | 1 | 8 |
| Phase 2: Multi-Omics & Clinical | 6 weeks | 9 | 14 |
| Phase 3: Analysis Router | 4 weeks | 15 | 18 |
| Phase 4: Ensemble Service | 4 weeks | 19 | 22 |
| Phase 5: Health Service & Reporting | 4 weeks | 23 | 26 |
| Phase 6: Frontend & UX | 4 weeks | 27 | 30 |
| Phase 7: Testing & Optimization | 4 weeks | 31 | 34 |
| Phase 8: Security & Deployment | 2 weeks | 35 | 36 |

**Total Duration**: 36 weeks (~9 months)

### 13.2 Key Milestones

- **Milestone 1** (Week 8): Core services operational (Genomic, Expression, GRN)
- **Milestone 2** (Week 14): Multi-omics and clinical integration complete
- **Milestone 3** (Week 18): Intelligent routing system operational
- **Milestone 4** (Week 22): Ensemble predictions working
- **Milestone 5** (Week 26): Unified health reports and recommendations
- **Milestone 6** (Week 30): Complete frontend with unified UX
- **Milestone 7** (Week 34): Testing and optimization complete
- **Milestone 8** (Week 36): Production launch

---

## 14. Success Metrics

### 14.1 Technical Metrics

- **Prediction Accuracy**: >90% (ensemble) vs >85% (individual)
- **Method Selection Accuracy**: >95%
- **Coverage**: Support 95%+ of patients with at least one method
- **API Latency**: <500ms (p95) for simple queries, <5s for predictions
- **System Uptime**: >99.9%
- **Test Coverage**: >85%

### 14.2 Business Metrics

- **User Adoption**: Target active users
- **Prediction Volume**: Number of predictions per month
- **User Satisfaction**: NPS score >60
- **Time to Value**: <24 hours from data upload to first prediction

### 14.3 Clinical Metrics

- **Clinical Validation**: Validation on independent datasets
- **Physician Adoption**: Number of physicians using the system
- **Clinical Outcomes**: Improvement in patient outcomes (long-term)
- **Method Agreement**: High agreement when multiple methods available

---

## 15. Advantages of Combined Approach

### 15.1 Complementary Strengths

1. **GRN Approach**:
   - Understands regulatory mechanisms
   - Captures gene-gene interactions
   - Provides mechanistic insights
   - Enables network-based drug targeting

2. **Non-GRN Approach**:
   - Faster analysis (PRS, signatures)
   - Works with limited data
   - Well-validated methods
   - Lower computational cost

3. **Combined**:
   - Best of both worlds
   - Higher accuracy through ensemble
   - Flexible data requirements
   - Comprehensive insights

### 15.2 Use Case Coverage

- **Full Data**: Use both approaches for maximum accuracy
- **Limited Data**: Use non-GRN methods with appropriate confidence
- **Expression Only**: Use both expression signatures and GRN
- **Genomic Only**: Use PRS and variant analysis
- **Longitudinal**: Track changes in both GRN and direct measures

---

## 16. Conclusion

This unified plan provides a comprehensive roadmap for building the most advanced personalized health platform by combining GRN and non-GRN approaches. The intelligent routing and ensemble systems ensure optimal method selection and maximum prediction accuracy, while maintaining flexibility for varying data availability.

The 36-week timeline is ambitious but achievable with the right team and resources. The phased approach allows for iterative development, early validation, and risk mitigation.

**Key Innovations**:
1. Intelligent method selection based on data availability
2. Ensemble predictions combining multiple approaches
3. Flexible fallback mechanisms
4. Unified user experience
5. Comprehensive evidence integration

This combined approach will provide the most accurate, comprehensive, and actionable personalized health insights available.

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Author**: GenNet Development Team  
**Status**: Draft - For Review

