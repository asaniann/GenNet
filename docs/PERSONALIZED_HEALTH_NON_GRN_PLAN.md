# Personalized Health Platform (Non-GRN Approach) - Detailed Implementation Plan

## Executive Summary

This document outlines a comprehensive plan for building a personalized health prediction system that achieves personalization through direct genomic analysis, expression signatures, multi-omics integration, clinical data fusion, and pharmacogenomics - **without requiring Gene Regulatory Network (GRN) modeling**. The system will be standalone but can optionally leverage GenNet services when available for enhanced analysis.

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Implementation Phases](#implementation-phases)
5. [Technical Specifications](#technical-specifications)
6. [Data Models](#data-models)
7. [API Design](#api-design)
8. [GenNet Integration (Optional)](#gennet-integration-optional)
9. [Security & Privacy](#security--privacy)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Plan](#deployment-plan)
12. [Timeline & Milestones](#timeline--milestones)

---

## 1. Project Overview

### 1.1 Objectives

- **Primary Goal**: Build a personalized health prediction system using direct analysis methods without GRN modeling
- **Key Capabilities**:
  - Genomic variant analysis and Polygenic Risk Scores (PRS)
  - Gene expression signature analysis and biomarker identification
  - Multi-omics data integration and fusion
  - Clinical data integration and decision support
  - Pharmacogenomics and drug response prediction
  - Ensemble predictions combining multiple methods
  - Optional integration with GenNet for enhanced analysis

### 1.2 Use Cases

1. **Disease Risk Assessment**
   - Patient submits genomic data (VCF file)
   - System calculates Polygenic Risk Scores for multiple diseases
   - Provides risk percentiles and actionable insights

2. **Expression-Based Diagnosis**
   - Patient submits RNA-seq or microarray data
   - System scores disease-specific expression signatures
   - Provides diagnostic and prognostic predictions

3. **Multi-Omics Health Profile**
   - Patient submits multiple omics data types
   - System integrates data for comprehensive health assessment
   - Provides unified health predictions

4. **Clinical Decision Support**
   - Integrates with Electronic Health Records (EHR)
   - Combines clinical data with genomic insights
   - Provides evidence-based recommendations

5. **Personalized Medicine**
   - Pharmacogenomics analysis for drug selection
   - Dosing recommendations based on genetic variants
   - Drug-drug interaction analysis

### 1.3 Success Criteria

- **Accuracy**: >85% disease prediction accuracy on validated datasets
- **Performance**: <30 seconds for PRS calculation, <5s for expression analysis
- **Scalability**: Support 10,000+ concurrent users
- **Compliance**: HIPAA/GDPR compliant
- **Integration**: Optional seamless integration with GenNet services

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  - Patient Dashboard                                         │
│  - Health Reports & Visualizations                          │
│  - Data Upload Interface                                     │
│  - Multi-omics Data Explorer                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  API Gateway (Kong)                          │
│  - Authentication                                            │
│  - Rate Limiting                                             │
│  - Request Routing                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│ Genomic      │ │ Expression  │ │ Clinical   │
│ Analysis     │ │ Analysis    │ │ Data       │
│ Service      │ │ Service     │ │ Service    │
└───────┬──────┘ └─────┬──────┘ └─────┬──────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│ Multi-Omics  │ │ Pharmaco-  │ │ Prediction │
│ Integration  │ │ genomics   │ │ Service    │
│ Service      │ │ Service    │ │            │
└───────┬──────┘ └─────┬──────┘ └─────┬──────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│ Patient Data │ │ Health     │ │ GenNet     │
│ Service      │ │ Service    │ │ Integration│
│              │ │            │ │ (Optional) │
└──────────────┘ └────────────┘ └────────────┘
```

### 2.2 New Services

1. **Genomic Analysis Service** (New)
   - Variant calling and annotation
   - Polygenic Risk Score (PRS) calculation
   - Variant pathogenicity prediction
   - Population frequency analysis

2. **Expression Analysis Service** (New)
   - Gene expression signature analysis
   - Biomarker identification
   - Expression-based disease classification
   - Pathway activity scoring

3. **Clinical Data Service** (New)
   - EHR integration (HL7 FHIR)
   - Clinical data normalization
   - Lab result interpretation
   - Medical history analysis

4. **Multi-Omics Integration Service** (New)
   - Multi-omics data fusion
   - Cross-omics correlation analysis
   - Integrated biomarker discovery
   - Multi-omics ML models

5. **Pharmacogenomics Service** (New)
   - Drug-gene interaction database
   - Drug response prediction
   - Pharmacokinetic modeling
   - Drug-drug interaction analysis

6. **Health Service** (New/Enhanced)
   - Risk score aggregation
   - Ensemble prediction methods
   - Health report generation
   - Recommendation engine

7. **GenNet Integration Service** (New - Optional)
   - Service discovery for GenNet
   - Optional GRN analysis routing
   - Hybrid prediction workflows

### 2.3 Data Flow

1. Patient uploads genomic/expression/clinical data via web UI
2. Data stored in S3 (raw files) and PostgreSQL (metadata)
3. Analysis services process data:
   - Genomic Analysis Service: Variant annotation, PRS calculation
   - Expression Analysis Service: Signature scoring, biomarker identification
   - Clinical Data Service: EHR integration, lab interpretation
4. Multi-Omics Service integrates results from multiple sources
5. Pharmacogenomics Service provides drug recommendations
6. Health Service aggregates predictions using ensemble methods
7. Optional: GenNet Integration Service routes to GenNet for GRN analysis
8. Results displayed in web UI with visualizations and reports

---

## 3. Core Components

### 3.1 Genomic Variant Analysis

#### 3.1.1 Polygenic Risk Scores (PRS)

**Methodology**:
- Use published PRS models from PGS Catalog
- Weighted sum of effect alleles
- Population-specific calibration
- Percentile ranking

**Implementation**:
```python
class PRSCalculator:
    def calculate_prs(
        self,
        variants: List[Variant],
        prs_model: PRSModel,
        population: str = "EUR"
    ) -> PRSResult:
        """
        Calculate PRS for a patient
        Returns score, percentile, confidence interval
        """
        pass
```

**Key Features**:
- Support for 100+ diseases with PRS models
- Population-specific calibration
- Confidence intervals
- Effect size interpretation

#### 3.1.2 Variant Annotation

**Annotation Sources**:
- **Functional Impact**: SIFT, PolyPhen-2, CADD, DANN
- **Population Frequency**: gnomAD, 1000 Genomes, ExAC
- **Clinical Significance**: ClinVar, OMIM
- **Pathway Associations**: KEGG, Reactome, GO

**Implementation Location**: `services/genomic-analysis-service/variant_annotator.py`

#### 3.1.3 Variant Filtering and Prioritization

- Filter by quality scores
- Prioritize by functional impact
- Filter by population frequency
- Clinical significance filtering

### 3.2 Expression-Based Analysis

#### 3.2.1 Gene Expression Signatures

**Signature Types**:
- **Disease Signatures**: Disease-specific gene expression patterns
- **Treatment Response Signatures**: Predict treatment efficacy
- **Prognostic Signatures**: Predict disease outcome
- **Pathway Signatures**: Pathway activity scores

**Scoring Methods**:
- **ssGSEA**: Single-sample Gene Set Enrichment Analysis
- **GSVA**: Gene Set Variation Analysis
- **Z-score**: Standardized expression scores
- **Signature Enrichment**: Enrichment-based scoring

**Implementation**:
```python
class ExpressionSignatureScorer:
    def score_signature(
        self,
        expression_data: pd.DataFrame,
        signature: ExpressionSignature
    ) -> float:
        """
        Score expression signature
        Returns signature score
        """
        pass
```

**Implementation Location**: `services/expression-analysis-service/signature_scorer.py`

#### 3.2.2 Biomarker Identification

- Differential expression analysis
- Multi-gene biomarker panels
- Expression thresholds
- Validation against reference datasets

#### 3.2.3 Disease Classification

- Expression-based disease classifiers
- Multi-class classification
- Confidence scores
- Feature importance analysis

### 3.3 Multi-Omics Integration

#### 3.3.1 Data Fusion Methods

1. **Early Fusion**
   - Concatenate features from all omics
   - Train single model on combined features
   - Simple but may suffer from curse of dimensionality

2. **Late Fusion**
   - Train separate models per omics type
   - Combine predictions using ensemble methods
   - Robust to missing data

3. **Intermediate Fusion**
   - Use autoencoders for feature extraction
   - Learn shared representations
   - Better capture cross-omics relationships

4. **Multi-View Learning**
   - Learn shared and omics-specific representations
   - Capture both common and unique patterns
   - State-of-the-art performance

**Implementation**:
```python
class MultiOmicsIntegrator:
    def integrate(
        self,
        genomic_data: GenomicProfile,
        expression_data: ExpressionProfile,
        proteomic_data: Optional[ProteomicProfile] = None,
        method: str = "multi_view"
    ) -> IntegratedProfile:
        """
        Integrate multiple omics data types
        Returns integrated profile with features
        """
        pass
```

**Implementation Location**: `services/multi-omics-service/data_fusion.py`

#### 3.3.2 Cross-Omics Analysis

- Correlation networks across omics
- Causal inference
- Multi-omics clustering
- Integrated pathway analysis

### 3.4 Clinical Data Integration

#### 3.4.1 EHR Integration

**HL7 FHIR Integration**:
- Patient demographics
- Medical history
- Lab results
- Medications
- Diagnoses

**Implementation**:
```python
class FHIRClient:
    def fetch_patient_data(
        self,
        patient_id: str,
        resource_types: List[str]
    ) -> Dict[str, Any]:
        """
        Fetch patient data from FHIR server
        """
        pass
```

**Implementation Location**: `services/clinical-data-service/fhir_client.py`

#### 3.4.2 Clinical Decision Support

- Risk stratification
- Alert generation
- Guideline adherence checking
- Treatment recommendations

#### 3.4.3 Lab Result Interpretation

- Normal range checking
- Trend analysis
- Critical value alerts
- Reference value adjustment

### 3.5 Pharmacogenomics

#### 3.5.1 Drug-Gene Interactions

**Key Genes**:
- **CYP450 Family**: Drug metabolism (CYP2D6, CYP2C19, CYP3A4, etc.)
- **Drug Transporters**: Uptake and efflux (ABCB1, SLC transporters)
- **Drug Targets**: Variants affecting drug binding
- **HLA**: Immune-mediated adverse reactions

**Implementation**:
```python
class DrugGeneInteractionDB:
    def get_interactions(
        self,
        patient_variants: List[Variant],
        drug_id: str
    ) -> List[DrugGeneInteraction]:
        """
        Get drug-gene interactions for patient
        """
        pass
```

**Implementation Location**: `services/pharmacogenomics-service/drug_gene_db.py`

#### 3.5.2 Drug Response Prediction

- Pharmacokinetic models (ADME)
- Pharmacodynamic models (target effects)
- Dosing recommendations
- Adverse event prediction

#### 3.5.3 Drug-Drug Interactions

- Metabolic interactions
- Transport interactions
- Target interactions
- Combined risk assessment

### 3.6 Ensemble Prediction

#### 3.6.1 Ensemble Methods

1. **Weighted Voting**
   - Weight predictions by method confidence
   - Method-specific weights learned from validation data

2. **Stacking**
   - Train meta-learner on method predictions
   - Learn optimal combination

3. **Bayesian Model Averaging**
   - Probabilistic combination
   - Uncertainty quantification

**Implementation**:
```python
class EnsemblePredictor:
    def predict(
        self,
        genomic_prediction: Optional[Prediction],
        expression_prediction: Optional[Prediction],
        multi_omics_prediction: Optional[Prediction],
        clinical_prediction: Optional[Prediction],
        method: str = "weighted_voting"
    ) -> EnsemblePrediction:
        """
        Combine predictions from multiple methods
        Returns ensemble prediction with confidence
        """
        pass
```

**Implementation Location**: `services/health-service/ensemble_predictor.py`

---

## 4. Implementation Phases

### Phase 1: Foundation & Genomic Analysis (Weeks 1-6)

**Goals**: Set up infrastructure and build genomic analysis capabilities

**Tasks**:
1. Create Patient Data Service
   - Database schema design
   - API endpoints for patient data CRUD
   - Data validation and sanitization
   - Privacy controls and anonymization

2. Build Genomic Analysis Service
   - VCF file parsing (using cyvcf2 or pysam)
   - Variant annotation pipeline
   - PRS calculation engine
   - Integration with external databases:
     - ClinVar API for clinical significance
     - gnomAD API for population frequencies
     - PGS Catalog for PRS models

3. Data Storage Setup
   - PostgreSQL for patient metadata and variants
   - S3 for raw VCF files
   - Redis for caching annotation results

4. Basic APIs
   - Upload VCF file
   - Get annotated variants
   - Calculate PRS for diseases
   - Get variant details

**Deliverables**:
- Patient Data Service deployed
- Genomic Analysis Service with PRS calculation
- Variant annotation pipeline operational
- Basic APIs functional
- Integration with ClinVar and gnomAD

**Key Files to Create**:
- `services/patient-data-service/main.py`
- `services/patient-data-service/models.py`
- `services/patient-data-service/database.py`
- `services/genomic-analysis-service/main.py`
- `services/genomic-analysis-service/variant_annotator.py`
- `services/genomic-analysis-service/prs_calculator.py`
- `services/genomic-analysis-service/vcf_parser.py`

### Phase 2: Expression Analysis (Weeks 7-10)

**Goals**: Build expression-based analysis capabilities

**Tasks**:
1. Build Expression Analysis Service
   - Expression data normalization (log2, quantile, etc.)
   - Signature scoring algorithms:
     - ssGSEA implementation
     - GSVA implementation
     - Z-score calculation
   - Biomarker identification
   - Disease classification models

2. Expression Signature Database
   - Curate disease-specific signatures
   - Treatment response signatures
   - Prognostic signatures
   - Reference expression datasets (GTEx, TCGA)

3. Integration
   - Connect to Patient Data Service
   - Expression-based prediction endpoints
   - Signature scoring APIs

**Deliverables**:
- Expression Analysis Service deployed
- Signature scoring algorithms implemented
- Expression-based disease prediction working
- Biomarker identification tools
- Signature database populated

**Key Files to Create**:
- `services/expression-analysis-service/main.py`
- `services/expression-analysis-service/signature_scorer.py`
- `services/expression-analysis-service/biomarker_finder.py`
- `services/expression-analysis-service/disease_classifier.py`
- `services/expression-analysis-service/normalizer.py`

### Phase 3: Clinical Data Integration (Weeks 11-14)

**Goals**: Integrate clinical data and build clinical decision support

**Tasks**:
1. Build Clinical Data Service
   - HL7 FHIR integration
   - FHIR resource parsing
   - Clinical data normalization
   - Lab result interpretation
   - Medical history extraction

2. Clinical Models
   - Risk stratification models
   - Clinical decision support rules
   - Guideline-based recommendations
   - Alert generation

3. Integration
   - Connect to Patient Data Service
   - Clinical prediction endpoints
   - EHR integration APIs

**Deliverables**:
- Clinical Data Service deployed
- FHIR integration working
- Clinical prediction models
- Lab result interpretation
- Clinical decision support rules

**Key Files to Create**:
- `services/clinical-data-service/main.py`
- `services/clinical-data-service/fhir_client.py`
- `services/clinical-data-service/clinical_models.py`
- `services/clinical-data-service/lab_interpreter.py`
- `services/clinical-data-service/decision_support.py`

### Phase 4: Multi-Omics Integration (Weeks 15-18)

**Goals**: Build multi-omics data fusion and integrated analysis

**Tasks**:
1. Build Multi-Omics Service
   - Data fusion algorithms:
     - Early fusion implementation
     - Late fusion (ensemble)
     - Intermediate fusion (autoencoders)
     - Multi-view learning
   - Multi-omics ML models
   - Cross-omics correlation analysis
   - Integrated pathway analysis

2. Model Training
   - Train multi-omics prediction models
   - Ensemble methods
   - Feature selection
   - Model validation

3. Integration
   - Connect all omics services
   - Multi-omics prediction endpoints
   - Integrated analysis APIs

**Deliverables**:
- Multi-Omics Service deployed
- Data fusion algorithms implemented
- Multi-omics prediction models trained
- Integrated analysis tools
- Cross-omics correlation analysis

**Key Files to Create**:
- `services/multi-omics-service/main.py`
- `services/multi-omics-service/data_fusion.py`
- `services/multi-omics-service/multi_omics_models.py`
- `services/multi-omics-service/correlation_analyzer.py`
- `services/multi-omics-service/pathway_analyzer.py`

### Phase 5: Pharmacogenomics (Weeks 19-22)

**Goals**: Build pharmacogenomics and drug response prediction

**Tasks**:
1. Build Pharmacogenomics Service
   - Drug-gene interaction database
   - Pharmacokinetic models (ADME)
   - Drug response prediction
   - Dosing recommendations
   - Drug-drug interaction analysis

2. Drug Databases Integration
   - DrugBank API integration
   - PharmGKB database integration
   - CYP450 variant database
   - Drug interaction database

3. Integration
   - Connect to Genomic Analysis Service
   - Drug recommendation endpoints
   - Dosing calculation APIs

**Deliverables**:
- Pharmacogenomics Service deployed
- Drug-gene interaction database populated
- Drug response prediction models
- Dosing recommendation engine
- Drug interaction analysis

**Key Files to Create**:
- `services/pharmacogenomics-service/main.py`
- `services/pharmacogenomics-service/drug_gene_db.py`
- `services/pharmacogenomics-service/response_predictor.py`
- `services/pharmacogenomics-service/dosing_calculator.py`
- `services/pharmacogenomics-service/interaction_analyzer.py`

### Phase 6: Health Service & Ensemble (Weeks 23-26)

**Goals**: Build health service with ensemble prediction methods

**Tasks**:
1. Build Health Service
   - Risk score aggregation
   - Ensemble prediction methods:
     - Weighted voting
     - Stacking
     - Bayesian model averaging
   - Health report generation
   - Recommendation engine

2. Ensemble Methods
   - Combine predictions from all methods
   - Learn optimal weights
   - Confidence calibration
   - Uncertainty quantification

3. Reporting
   - PDF report generation
   - Interactive visualizations
   - Export capabilities
   - Customizable report templates

**Deliverables**:
- Health Service deployed
- Ensemble prediction methods implemented
- Health report generation
- Recommendation engine
- Visualization components

**Key Files to Create**:
- `services/health-service/main.py`
- `services/health-service/ensemble_predictor.py`
- `services/health-service/report_generator.py`
- `services/health-service/recommendation_engine.py`
- `services/health-service/risk_aggregator.py`

### Phase 7: GenNet Integration (Optional) (Weeks 27-28)

**Goals**: Optional integration with GenNet for enhanced analysis

**Tasks**:
1. Build GenNet Integration Service
   - Service discovery for GenNet services
   - Optional GRN analysis routing
   - Result fusion with non-GRN methods

2. Hybrid Workflows
   - Use GRN when available
   - Fallback to non-GRN methods
   - Combine GRN and non-GRN predictions
   - Enhanced ensemble with GRN

**Deliverables**:
- GenNet Integration Service
- Hybrid prediction workflows
- Optional GRN enhancement
- Service discovery working

**Key Files to Create**:
- `services/gennet-integration-service/main.py`
- `services/gennet-integration-service/service_discovery.py`
- `services/gennet-integration-service/hybrid_predictor.py`
- `services/gennet-integration-service/grn_router.py`

### Phase 8: Frontend & Testing (Weeks 29-32)

**Goals**: Build frontend and comprehensive testing

**Tasks**:
1. Frontend Development
   - Patient dashboard
   - Data upload interface
   - Health reports visualization
   - Prediction results display
   - Multi-omics data explorer

2. Testing
   - Unit tests (>80% coverage)
   - Integration tests
   - End-to-end tests
   - Performance testing
   - Security testing

3. Documentation
   - API documentation
   - User guides
   - Developer documentation
   - Deployment guides

**Deliverables**:
- Complete frontend
- Test suite
- Documentation
- Production-ready system

---

## 5. Technical Specifications

### 5.1 Technology Stack

#### Backend Services
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Databases**:
  - PostgreSQL 15+ (patient metadata, variants, clinical data)
  - Redis 7+ (caching, sessions)
  - InfluxDB 2+ (time-series clinical data)
- **Storage**: AWS S3 (genomic files, expression data)
- **Message Queue**: RabbitMQ or AWS SQS
- **ML Framework**: scikit-learn, XGBoost, PyTorch, TensorFlow

#### Genomics Libraries
- **VCF Parsing**: cyvcf2, pysam
- **Variant Annotation**: VEP (Variant Effect Predictor), SnpEff
- **Genomics**: pandas, numpy, scipy

#### Clinical Libraries
- **FHIR**: fhir.resources, fhirclient
- **HL7**: hl7

#### Frontend
- **Framework**: Next.js 14+
- **Language**: TypeScript
- **Visualization**: D3.js, Plotly, Recharts
- **UI Components**: Tailwind CSS, shadcn/ui

#### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **Cloud**: AWS (EKS, RDS, S3, ElastiCache)
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack

### 5.2 Performance Requirements

- **PRS Calculation**: <30 seconds for typical VCF files
- **Expression Analysis**: <5 seconds for signature scoring
- **Multi-Omics Integration**: <10 seconds for data fusion
- **API Response Time**: <500ms for simple queries, <5s for predictions
- **Concurrent Users**: Support 10,000+ concurrent users
- **Data Processing**: Process 1000+ patient datasets per hour

### 5.3 Scalability Considerations

- **Horizontal Scaling**: All services stateless, horizontally scalable
- **Database Sharding**: Patient data sharded by patient_id
- **Caching**: Multi-layer caching (Redis, CDN)
- **Async Processing**: Background jobs for heavy computations
- **Load Balancing**: Kubernetes service mesh with Istio

---

## 6. Data Models

### 6.1 Patient Model

```python
class Patient(Base):
    __tablename__ = "patients"
    
    id: str = Column(String, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("users.id"))
    anonymized_id: str = Column(String, unique=True, index=True)
    
    # Demographics (anonymized)
    age_range: str = Column(String)
    gender: Optional[str] = Column(String)
    ethnicity: Optional[str] = Column(String)
    
    # Metadata
    created_at: datetime = Column(DateTime)
    updated_at: datetime = Column(DateTime)
    consent_given: bool = Column(Boolean)
    consent_date: Optional[datetime] = Column(DateTime)
    
    # Relationships
    genomic_profiles: List["GenomicProfile"]
    expression_profiles: List["ExpressionProfile"]
    clinical_data: List["ClinicalData"]
    health_predictions: List["HealthPrediction"]
```

### 6.2 Genomic Profile Model

```python
class GenomicProfile(Base):
    __tablename__ = "genomic_profiles"
    
    id: str = Column(String, primary_key=True)
    patient_id: str = Column(String, ForeignKey("patients.id"))
    
    # File storage
    vcf_file_s3_key: str = Column(String)
    vcf_file_size: int = Column(Integer)
    
    # Processing metadata
    variant_count: int = Column(Integer)
    processing_status: str = Column(String)
    annotation_version: str = Column(String)
    
    # Timestamps
    created_at: datetime = Column(DateTime)
    processed_at: Optional[datetime] = Column(DateTime)
```

### 6.3 Variant Model

```python
class Variant(Base):
    __tablename__ = "variants"
    
    id: str = Column(String, primary_key=True)
    genomic_profile_id: str = Column(String, ForeignKey("genomic_profiles.id"))
    
    # Variant coordinates
    chromosome: str = Column(String)
    position: int = Column(Integer)
    ref_allele: str = Column(String)
    alt_allele: str = Column(String)
    
    # Annotation
    gene: Optional[str] = Column(String)
    consequence: Optional[str] = Column(String)
    impact: Optional[str] = Column(String)  # HIGH, MODERATE, LOW, MODIFIER
    sift_score: Optional[float] = Column(Float)
    polyphen_score: Optional[float] = Column(Float)
    cadd_score: Optional[float] = Column(Float)
    
    # Population frequency
    gnomad_af: Optional[float] = Column(Float)
    gnomad_popmax_af: Optional[float] = Column(Float)
    
    # Clinical significance
    clinvar_significance: Optional[str] = Column(String)
    clinvar_review: Optional[str] = Column(String)
    
    # Genotype
    genotype: str = Column(String)  # "0/1", "1/1", etc.
    quality: float = Column(Float)
```

### 6.4 PRS Score Model

```python
class PRSScore(Base):
    __tablename__ = "prs_scores"
    
    id: str = Column(String, primary_key=True)
    genomic_profile_id: str = Column(String, ForeignKey("genomic_profiles.id"))
    
    # PRS details
    disease_code: str = Column(String)  # ICD-10 or custom
    disease_name: str = Column(String)
    prs_model_id: str = Column(String)  # PGS Catalog ID
    prs_model_version: str = Column(String)
    
    # Scores
    prs_score: float = Column(Float)
    percentile: float = Column(Float)  # Population percentile
    z_score: float = Column(Float)
    
    # Confidence
    confidence_interval_lower: float = Column(Float)
    confidence_interval_upper: float = Column(Float)
    
    # Metadata
    variant_count: int = Column(Integer)
    population: str = Column(String)  # EUR, AFR, ASN, etc.
    calculated_at: datetime = Column(DateTime)
```

### 6.5 Expression Profile Model

```python
class ExpressionProfile(Base):
    __tablename__ = "expression_profiles"
    
    id: str = Column(String, primary_key=True)
    patient_id: str = Column(String, ForeignKey("patients.id"))
    
    # Data details
    tissue_type: str = Column(String)
    sample_date: datetime = Column(DateTime)
    platform: str = Column(String)  # "rna_seq", "microarray"
    
    # File storage
    expression_file_s3_key: str = Column(String)
    normalized_file_s3_key: Optional[str] = Column(String)
    
    # Metadata
    gene_count: int = Column(Integer)
    sample_count: int = Column(Integer)
    processing_status: str = Column(String)
    
    # Timestamps
    created_at: datetime = Column(DateTime)
    processed_at: Optional[datetime] = Column(DateTime)
```

### 6.6 Signature Score Model

```python
class SignatureScore(Base):
    __tablename__ = "signature_scores"
    
    id: str = Column(String, primary_key=True)
    expression_profile_id: str = Column(String, ForeignKey("expression_profiles.id"))
    
    # Signature details
    signature_id: str = Column(String)
    signature_name: str = Column(String)
    signature_type: str = Column(String)  # "disease", "treatment", "prognostic"
    
    # Score
    score: float = Column(Float)
    percentile: Optional[float] = Column(Float)
    p_value: Optional[float] = Column(Float)
    
    # Method
    scoring_method: str = Column(String)  # "ssGSEA", "GSVA", "z_score"
    
    # Timestamps
    calculated_at: datetime = Column(DateTime)
```

### 6.7 Multi-Omics Profile Model

```python
class MultiOmicsProfile(Base):
    __tablename__ = "multi_omics_profiles"
    
    id: str = Column(String, primary_key=True)
    patient_id: str = Column(String, ForeignKey("patients.id"))
    
    # Component profiles
    genomic_profile_id: Optional[str] = Column(String)
    expression_profile_id: Optional[str] = Column(String)
    proteomic_profile_id: Optional[str] = Column(String)
    metabolomic_profile_id: Optional[str] = Column(String)
    
    # Integration
    fusion_method: str = Column(String)  # "early", "late", "intermediate", "multi_view"
    integrated_features: Dict = Column(JSON)  # Combined feature vector
    
    # Metadata
    feature_count: int = Column(Integer)
    created_at: datetime = Column(DateTime)
```

### 6.8 Health Prediction Model

```python
class HealthPrediction(Base):
    __tablename__ = "health_predictions"
    
    id: str = Column(String, primary_key=True)
    patient_id: str = Column(String, ForeignKey("patients.id"))
    
    # Prediction details
    prediction_type: str = Column(String)  # "disease_risk", "drug_response", etc.
    disease_code: str = Column(String)
    disease_name: str = Column(String)
    
    # Methods used
    methods: List[str] = Column(JSON)  # ["prs", "expression", "multi_omics", "clinical"]
    is_ensemble: bool = Column(Boolean)
    
    # Scores
    risk_score: float = Column(Float)  # 0-100
    confidence_interval_lower: float = Column(Float)
    confidence_interval_upper: float = Column(Float)
    confidence_level: float = Column(Float)  # 0-1
    
    # Evidence
    genomic_evidence: Optional[Dict] = Column(JSON)
    expression_evidence: Optional[Dict] = Column(JSON)
    clinical_evidence: Optional[Dict] = Column(JSON)
    
    # Metadata
    model_version: str = Column(String)
    prediction_date: datetime = Column(DateTime)
    created_at: datetime = Column(DateTime)
```

### 6.9 Drug Recommendation Model

```python
class DrugRecommendation(Base):
    __tablename__ = "drug_recommendations"
    
    id: str = Column(String, primary_key=True)
    patient_id: str = Column(String, ForeignKey("patients.id"))
    health_prediction_id: Optional[str] = Column(String, ForeignKey("health_predictions.id"))
    
    # Drug information
    drug_name: str = Column(String)
    drug_id: str = Column(String)  # DrugBank ID
    mechanism_of_action: str = Column(String)
    
    # Prediction
    predicted_response: str = Column(String)  # "positive", "negative", "neutral"
    response_score: float = Column(Float)  # 0-1
    confidence: float = Column(Float)
    
    # Pharmacogenomics
    relevant_variants: List[str] = Column(JSON)  # Variant IDs
    cyp450_metabolism: Optional[Dict] = Column(JSON)
    dosing_recommendation: Optional[Dict] = Column(JSON)
    
    # Interactions
    drug_interactions: List[Dict] = Column(JSON)
    contraindications: List[str] = Column(JSON)
    
    # Metadata
    recommendation_date: datetime = Column(DateTime)
    model_version: str = Column(String)
```

---

## 7. API Design

### 7.1 Genomic Analysis Service APIs

#### Upload VCF File
```http
POST /api/v1/genomic/upload
Content-Type: multipart/form-data

{
  "file": <VCF file>,
  "patient_id": "patient-123"
}

Response: 202 Accepted
{
  "genomic_profile_id": "genomic-456",
  "processing_status": "uploaded",
  "estimated_completion": "2024-01-15T10:05:00Z"
}
```

#### Get Annotated Variants
```http
GET /api/v1/genomic/{genomic_profile_id}/variants
Query: ?gene=BRCA1&impact=high&limit=100

Response: 200 OK
{
  "variants": [
    {
      "id": "var-789",
      "chromosome": "17",
      "position": 43044295,
      "ref_allele": "G",
      "alt_allele": "A",
      "gene": "BRCA1",
      "consequence": "missense_variant",
      "impact": "HIGH",
      "cadd_score": 28.5,
      "gnomad_af": 0.0001,
      "clinvar_significance": "Pathogenic",
      "genotype": "0/1"
    }
  ],
  "total": 1500,
  "filtered": 5
}
```

#### Calculate PRS
```http
POST /api/v1/genomic/{genomic_profile_id}/prs
Content-Type: application/json

{
  "diseases": ["ICD10:C50", "ICD10:I25"],
  "population": "EUR"
}

Response: 200 OK
{
  "prs_scores": [
    {
      "disease_code": "ICD10:C50",
      "disease_name": "Breast Cancer",
      "prs_score": 1.25,
      "percentile": 85.3,
      "z_score": 1.05,
      "confidence_interval": [1.10, 1.40],
      "variant_count": 1200,
      "prs_model_id": "PGS000018"
    }
  ]
}
```

### 7.2 Expression Analysis Service APIs

#### Upload Expression Data
```http
POST /api/v1/expression/upload
Content-Type: multipart/form-data

{
  "file": <CSV/TSV file>,
  "patient_id": "patient-123",
  "tissue_type": "blood",
  "platform": "rna_seq"
}

Response: 202 Accepted
{
  "expression_profile_id": "expr-456",
  "processing_status": "uploaded"
}
```

#### Score Signatures
```http
POST /api/v1/expression/{expression_profile_id}/signatures
Content-Type: application/json

{
  "signatures": ["disease_breast_cancer", "treatment_tamoxifen"],
  "method": "ssGSEA"
}

Response: 200 OK
{
  "scores": [
    {
      "signature_id": "disease_breast_cancer",
      "signature_name": "Breast Cancer Signature",
      "score": 0.75,
      "percentile": 92.5,
      "p_value": 0.001,
      "method": "ssGSEA"
    }
  ]
}
```

#### Classify Disease
```http
POST /api/v1/expression/{expression_profile_id}/classify
Content-Type: application/json

{
  "disease_types": ["breast_cancer", "lung_cancer", "colorectal_cancer"]
}

Response: 200 OK
{
  "predictions": [
    {
      "disease": "breast_cancer",
      "probability": 0.85,
      "confidence": 0.90,
      "top_genes": ["ESR1", "ERBB2", "PGR"]
    }
  ]
}
```

### 7.3 Multi-Omics Service APIs

#### Integrate Omics Data
```http
POST /api/v1/multi-omics/integrate
Content-Type: application/json

{
  "patient_id": "patient-123",
  "genomic_profile_id": "genomic-456",
  "expression_profile_id": "expr-789",
  "fusion_method": "multi_view"
}

Response: 200 OK
{
  "multi_omics_profile_id": "multi-abc",
  "feature_count": 5000,
  "fusion_method": "multi_view",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Predict from Multi-Omics
```http
POST /api/v1/multi-omics/{multi_omics_profile_id}/predict
Content-Type: application/json

{
  "disease": "ICD10:C50",
  "model_version": "v2.1"
}

Response: 200 OK
{
  "prediction": {
    "disease_code": "ICD10:C50",
    "disease_name": "Breast Cancer",
    "risk_score": 78.5,
    "confidence": 0.88,
    "method": "multi_omics",
    "contributing_features": {
      "genomic": 0.40,
      "expression": 0.35,
      "interaction": 0.25
    }
  }
}
```

### 7.4 Pharmacogenomics Service APIs

#### Get Drug Response
```http
GET /api/v1/pharmacogenomics/{patient_id}/drug-response
Query: ?drug=DB00675

Response: 200 OK
{
  "drug_id": "DB00675",
  "drug_name": "Tamoxifen",
  "predicted_response": "positive",
  "response_score": 0.85,
  "confidence": 0.82,
  "relevant_variants": [
    {
      "variant_id": "var-123",
      "gene": "CYP2D6",
      "impact": "Poor metabolizer",
      "effect": "Reduced efficacy"
    }
  ],
  "dosing_recommendation": {
    "standard_dose": "20mg daily",
    "recommended_dose": "40mg daily",
    "rationale": "CYP2D6 poor metabolizer requires higher dose"
  }
}
```

#### Get Drug Interactions
```http
GET /api/v1/pharmacogenomics/{patient_id}/interactions
Query: ?drugs=DB00675,DB01234

Response: 200 OK
{
  "interactions": [
    {
      "drug1": "DB00675",
      "drug2": "DB01234",
      "interaction_type": "metabolic",
      "severity": "moderate",
      "description": "CYP2D6 competitive inhibition",
      "recommendation": "Monitor for adverse effects"
    }
  ]
}
```

### 7.5 Health Service APIs

#### Ensemble Prediction
```http
POST /api/v1/health/{patient_id}/predict
Content-Type: application/json

{
  "disease": "ICD10:C50",
  "methods": ["prs", "expression", "multi_omics", "clinical"],
  "ensemble_method": "weighted_voting"
}

Response: 200 OK
{
  "ensemble_prediction": {
    "disease_code": "ICD10:C50",
    "disease_name": "Breast Cancer",
    "risk_score": 75.5,
    "confidence": 0.90,
    "ensemble_method": "weighted_voting",
    "individual_predictions": [
      {
        "method": "prs",
        "risk_score": 72.5,
        "weight": 0.30,
        "confidence": 0.89
      },
      {
        "method": "expression",
        "risk_score": 78.0,
        "weight": 0.35,
        "confidence": 0.92
      },
      {
        "method": "multi_omics",
        "risk_score": 76.0,
        "weight": 0.25,
        "confidence": 0.88
      },
      {
        "method": "clinical",
        "risk_score": 73.0,
        "weight": 0.10,
        "confidence": 0.75
      }
    ],
    "evidence_summary": {
      "genomic_evidence": "High PRS (85th percentile)",
      "expression_evidence": "Strong disease signature (p<0.001)",
      "clinical_evidence": "Family history, age 45"
    }
  }
}
```

#### Generate Health Report
```http
POST /api/v1/health/{patient_id}/reports
Content-Type: application/json

{
  "include_predictions": true,
  "include_recommendations": true,
  "include_pharmacogenomics": true,
  "format": "pdf"
}

Response: 202 Accepted
{
  "report_id": "report-789",
  "status": "generating",
  "estimated_completion": "2024-01-15T10:02:00Z"
}
```

---

## 8. GenNet Integration (Optional)

### 8.1 Integration Strategy

The system can optionally integrate with GenNet services for enhanced analysis:

1. **Service Discovery**: Detect available GenNet services
2. **Optional GRN Analysis**: If patient has expression data, optionally run GRN inference
3. **Hybrid Predictions**: Combine GRN-based predictions with non-GRN methods
4. **Network Visualization**: Use GenNet for network visualization if GRN available

### 8.2 Integration Service

**Location**: `services/gennet-integration-service/`

**Key Components**:
- Service discovery for GenNet services
- Optional routing to GenNet ML Service for GRN inference
- Hybrid prediction workflows
- Result fusion

**Implementation**:
```python
class GenNetIntegrationService:
    def discover_services(self) -> Dict[str, bool]:
        """Discover available GenNet services"""
        pass
    
    def optional_grn_analysis(
        self,
        expression_profile_id: str
    ) -> Optional[GRNResult]:
        """Optionally run GRN analysis if service available"""
        pass
    
    def hybrid_predict(
        self,
        non_grn_predictions: List[Prediction],
        grn_prediction: Optional[Prediction]
    ) -> EnsemblePrediction:
        """Combine GRN and non-GRN predictions"""
        pass
```

### 8.3 Hybrid Workflows

1. **Primary Path**: Use non-GRN methods (PRS, expression, multi-omics)
2. **Enhancement Path**: If GenNet available and expression data present, add GRN analysis
3. **Ensemble**: Combine all available predictions

---

## 9. Security & Privacy

### 9.1 Data Security

- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Access Control**: RBAC, JWT authentication
- **Data Isolation**: Multi-tenant isolation
- **Key Management**: AWS KMS

### 9.2 Privacy Protection

- **Anonymization**: Patient IDs anonymized
- **De-identification**: Remove PII from genomic data
- **Consent Management**: Track and enforce consent
- **Data Minimization**: Store only necessary data

### 9.3 Compliance

- **HIPAA**: Full compliance
- **GDPR**: Right to access, erasure, portability
- **Audit Logging**: Comprehensive audit trails
- **Data Retention**: Configurable retention policies

---

## 10. Testing Strategy

### 10.1 Unit Testing

- **Coverage Target**: >80%
- **Focus**: Business logic, data models, algorithms

### 10.2 Integration Testing

- Service-to-service communication
- Database operations
- External API integration
- End-to-end workflows

### 10.3 Performance Testing

- Load testing (10,000+ users)
- Stress testing
- Scalability testing
- Latency testing

### 10.4 Clinical Validation

- Model validation on independent datasets
- Accuracy testing
- Bias testing
- Reproducibility

---

## 11. Deployment Plan

### 11.1 Infrastructure

- **AWS EKS**: Kubernetes cluster
- **RDS**: PostgreSQL databases
- **S3**: File storage
- **ElastiCache**: Redis caching
- **VPC**: Network isolation

### 11.2 Deployment Strategy

- **Blue-Green**: Zero-downtime deployments
- **Canary**: Gradual rollouts
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack

---

## 12. Timeline & Milestones

### 12.1 Phase Timeline

| Phase | Duration | Start Week | End Week |
|-------|----------|------------|----------|
| Phase 1: Foundation & Genomic | 6 weeks | 1 | 6 |
| Phase 2: Expression Analysis | 4 weeks | 7 | 10 |
| Phase 3: Clinical Integration | 4 weeks | 11 | 14 |
| Phase 4: Multi-Omics | 4 weeks | 15 | 18 |
| Phase 5: Pharmacogenomics | 4 weeks | 19 | 22 |
| Phase 6: Health Service & Ensemble | 4 weeks | 23 | 26 |
| Phase 7: GenNet Integration | 2 weeks | 27 | 28 |
| Phase 8: Frontend & Testing | 4 weeks | 29 | 32 |

**Total Duration**: 32 weeks (~8 months)

### 12.2 Key Milestones

- **Milestone 1** (Week 6): Genomic analysis operational
- **Milestone 2** (Week 10): Expression analysis operational
- **Milestone 3** (Week 14): Clinical integration complete
- **Milestone 4** (Week 18): Multi-omics integration complete
- **Milestone 5** (Week 22): Pharmacogenomics complete
- **Milestone 6** (Week 26): Ensemble predictions working
- **Milestone 7** (Week 28): GenNet integration (optional)
- **Milestone 8** (Week 32): Production launch

---

## 13. Success Metrics

- **Prediction Accuracy**: >85% on validated datasets
- **API Latency**: <500ms (p95) for simple queries, <5s for predictions
- **System Uptime**: >99.9%
- **Test Coverage**: >80%
- **User Adoption**: Target active users

---

## 14. Conclusion

This plan provides a comprehensive roadmap for building a personalized health platform without requiring GRN modeling. The system uses direct genomic analysis, expression signatures, multi-omics integration, clinical data, and pharmacogenomics to achieve personalization. Optional GenNet integration allows for enhanced analysis when GRN data is available.

The 32-week timeline is achievable with the right team and resources. Regular milestone reviews and risk assessments will ensure the project stays on track.

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Author**: GenNet Development Team  
**Status**: Draft - For Review

