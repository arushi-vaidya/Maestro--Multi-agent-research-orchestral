# AKGP - Adaptive Knowledge Graph Protocol

**Version:** 1.0.0
**Project:** PharmaGraph - Drug Repurposing Knowledge Graph
**Module:** AKGP (Adaptive Knowledge Graph Protocol)

---

## Table of Contents

1. [Overview](#overview)
2. [Design Philosophy](#design-philosophy)
3. [Architecture](#architecture)
4. [Schema](#schema)
5. [Core Components](#core-components)
6. [Temporal Logic](#temporal-logic)
7. [Conflict Resolution](#conflict-resolution)
8. [Provenance Tracking](#provenance-tracking)
9. [Usage Examples](#usage-examples)
10. [How AKGP Differs from Static Knowledge Graphs](#how-akgp-differs-from-static-knowledge-graphs)
11. [Research Contribution](#research-contribution)

---

## Overview

**AKGP (Adaptive Knowledge Graph Protocol)** is a novel knowledge graph system designed specifically for pharmaceutical drug repurposing research. Unlike static knowledge graphs, AKGP:

- **Adapts over time** through temporal validity and recency weighting
- **Handles conflicts** by recording all evidence (never overwriting)
- **Tracks complete provenance** for regulatory auditability
- **Provides explainable results** through deterministic reasoning
- **Integrates multi-agent evidence** from clinical trials, patents, and market intelligence

AKGP is the core scientific contribution of the PharmaGraph system.

---

## Design Philosophy

### 1. **Provenance-First**
Every piece of evidence must be traceable to its source (agent, API, raw reference). This enables:
- Regulatory compliance
- Reproducibility
- Trust in AI-driven recommendations

### 2. **Conflict-Aware**
Conflicting evidence is **recorded, not overwritten**. AKGP:
- Detects contradictions between evidence
- Ranks evidence by quality, confidence, and recency
- Provides resolution recommendations with explanations

### 3. **Temporally Adaptive**
Evidence has temporal validity and recency weights:
- Recent evidence is weighted higher (but not automatically better)
- Evidence can expire (e.g., 2-year-old market forecasts)
- Historical evidence is retained for trend analysis

### 4. **Deterministic & Explainable**
All decisions are rule-based (no black-box ML):
- Weighting formulas are transparent
- Conflict detection uses explicit rules
- Query results include explanations

### 5. **Agent-Agnostic**
AKGP ingests structured outputs from any agent:
- Clinical Trials Agent
- Patent Intelligence Agent
- Market Intelligence Agent
- (Future: Literature Agent, Genomics Agent, etc.)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         AKGP MODULES                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Schema     │  │Provenance    │  │  Temporal    │     │
│  │   (.py)      │  │Tracker       │  │  Reasoner    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Conflict    │  │  Ingestion   │  │    Query     │     │
│  │  Detector    │  │   Engine     │  │    Engine    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Graph Manager (Neo4j + In-Memory)        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
            ┌─────────────────────────┐
            │   Neo4j Graph Database   │
            │  (or In-Memory Fallback) │
            └─────────────────────────┘
```

---

## Schema

### Node Types

| Node Type | Description | Key Fields |
|-----------|-------------|------------|
| **Drug** | Pharmaceutical compound | name, umls_id, drugbank_id, drug_class |
| **Disease** | Medical condition/indication | name, umls_id, icd10_code, disease_category |
| **Evidence** | Evidence from agents | agent_name, raw_reference, source_type, quality, confidence |
| **Trial** | Clinical trial | nct_id, phase, status, interventions, conditions |
| **Patent** | Patent filing | patent_number, assignees, grant_date, expiration_date |
| **MarketSignal** | Market intelligence | signal_type, market_size, growth_rate, forecast_year |

### Relationship Types

| Relationship | Source → Target | Meaning | Evidence Source |
|--------------|-----------------|---------|-----------------|
| **TREATS** | Drug → Disease | Established treatment | Clinical trials (Phase 3+) |
| **INVESTIGATED_FOR** | Drug → Disease | Under investigation | Clinical trials (any phase) |
| **SUGGESTS** | Drug → Disease | Potential repurposing | Patents, market intelligence |
| **CONTRADICTS** | Evidence → Evidence | Conflicting signals | Conflict detection |
| **SUPPORTS** | Evidence → Evidence | Corroborating signals | Provenance analysis |

### Temporal Fields

All evidence nodes have:
- `validity_start` (datetime): When evidence becomes valid
- `validity_end` (datetime, nullable): When evidence expires (None = indefinite)
- `extraction_timestamp` (datetime): When agent extracted this evidence

### Provenance Fields

All evidence nodes have:
- `agent_name` (str): Name of agent (e.g., "Clinical Trials Agent")
- `agent_id` (str): Agent identifier (e.g., "clinical")
- `api_source` (str): API used (e.g., "ClinicalTrials.gov")
- `raw_reference` (str): Raw reference (NCT ID, patent number, URL)
- `extraction_timestamp` (datetime): When evidence was extracted

---

## Core Components

### 1. **schema.py** - Data Models

Defines all node and relationship types using Pydantic for validation:

```python
from akgp.schema import DrugNode, DiseaseNode, EvidenceNode

drug = DrugNode(
    name="Metformin",
    source="Clinical Trials Agent",
    umls_id="C0025598",
    drug_class="Biguanide"
)
```

**Key Features:**
- Pydantic validation
- Type safety
- Extensible metadata
- Auto-generated UUIDs

### 2. **graph_manager.py** - Graph Database

Manages Neo4j operations with graceful degradation to in-memory mode:

```python
from akgp.graph_manager import GraphManager

# Neo4j mode (production)
graph = GraphManager(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)

# In-memory mode (testing)
graph = GraphManager(use_in_memory=True)

# CRUD operations
drug_id = graph.create_node(drug)
drug_data = graph.get_node(drug_id)
graph.update_node(drug_id, {"drug_class": "Antidiabetic"})
```

**Key Features:**
- Automatic fallback to in-memory if Neo4j unavailable
- Transaction safety
- Batch operations
- Search by name, type, etc.

### 3. **provenance.py** - Provenance Tracking

Tracks complete lineage of all evidence:

```python
from akgp.provenance import ProvenanceTracker

tracker = ProvenanceTracker()

# Record provenance
chain = tracker.record_provenance(evidence_node)

# Query provenance
evidence_from_clinical_agent = tracker.get_evidence_by_agent("clinical")
high_quality_evidence = tracker.get_evidence_by_quality(EvidenceQuality.HIGH)

# Generate audit report
report = tracker.generate_audit_report()
```

**Key Features:**
- Complete audit trails
- Source quality assessment (deterministic)
- Filtering by agent, source type, quality
- Regulatory compliance support

### 4. **temporal.py** - Temporal Logic

Handles time-based reasoning and recency weighting:

```python
from akgp.temporal import TemporalReasoner

reasoner = TemporalReasoner()

# Check validity
is_valid = reasoner.is_valid(evidence_node)

# Compute recency weight (exponential decay)
recency_weight = reasoner.compute_recency_weight(evidence_node)

# Compute combined weight
combined_weight = reasoner.compute_combined_weight(evidence_node)

# Get strongest evidence
strongest = reasoner.get_strongest_evidence(evidence_list, top_k=3)
```

**Recency Weighting Formula:**
```
weight = 2^(-age_days / half_life)

where:
  age_days = time since extraction
  half_life = configured per source type
    - Clinical: 730 days (2 years)
    - Patent: 1095 days (3 years)
    - Literature: 365 days (1 year)
    - Market: 180 days (6 months)
```

**Combined Weight Formula:**
```
combined_weight = base_quality × confidence × recency_weight / MAX_BOOST

where:
  base_quality = 0.9 (HIGH), 0.7 (MEDIUM), 0.5 (LOW)
  confidence = evidence confidence score (0.0-1.0)
  recency_weight = exponential decay weight
  MAX_BOOST = 2.0 (normalization factor)
```

### 5. **conflict_resolution.py** - Conflict Detection

Detects and resolves conflicts deterministically:

```python
from akgp.conflict_resolution import ConflictDetector

detector = ConflictDetector()

# Detect conflicts
conflicts = detector.detect_conflicts(evidence_list, drug_name="Metformin", disease_name="Cancer")

# Resolve conflict
for conflict in conflicts:
    resolution = detector.resolve_conflict(conflict, evidence1, evidence2)
    print(resolution['explanation'])
```

**Conflict Rules:**

1. **Efficacy Contradiction**: One evidence says "effective", another says "ineffective"
2. **Temporal Invalidation**: Newer Phase 3 trial supersedes older Phase 1 results
3. **Source Disagreement**: Clinical trial failure vs. patent filing

**Severity Assessment:**
- **High**: Both evidence have confidence > 0.7
- **Medium**: At least one has confidence > 0.5
- **Low**: Both have confidence ≤ 0.5

### 6. **ingestion.py** - Agent Output Ingestion

Ingests structured agent outputs into the graph:

```python
from akgp.ingestion import IngestionEngine

ingestion = IngestionEngine(graph_manager)

# Ingest clinical trial
result = ingestion.ingest_clinical_trial({
    "nct_id": "NCT12345678",
    "title": "Metformin for Colorectal Cancer Prevention",
    "interventions": ["Metformin"],
    "conditions": ["Colorectal Cancer"],
    "phase": "Phase 3",
    "status": "Completed",
    "confidence_score": 0.85
})

# Ingest patent
result = ingestion.ingest_patent({
    "patent_number": "US1234567",
    "title": "Use of Metformin for Cancer Treatment",
    "drugs": ["Metformin"],
    "indications": ["Cancer"],
    "confidence_score": 0.65
})

# Batch ingestion
results = ingestion.ingest_batch([
    ("clinical", trial_data),
    ("patent", patent_data),
    ("market", market_data)
], detect_conflicts=True)
```

**Auto-creation:**
- Automatically creates Drug and Disease nodes if they don't exist
- Links evidence to entities via relationships
- Runs conflict detection after batch ingestion

### 7. **query_engine.py** - Query Interface

High-level query interface with explanations:

```python
from akgp.query_engine import QueryEngine

query = QueryEngine(graph_manager)

# Query: "What evidence supports Drug X for Disease Y?"
result = query.query_drug_disease_evidence(
    drug_name="Metformin",
    disease_name="Colorectal Cancer"
)

print(result['explanation'])
# "Found 5 pieces of evidence for Metformin treating Colorectal Cancer.
#  Sources: 3 clinical, 1 patent, 1 market.
#  Strongest evidence: clinical from Clinical Trials Agent (weight: 0.856, confidence: 90%)."

# Query: "Are there conflicting signals?"
conflicts = query.query_conflicts(
    drug_name="Metformin",
    disease_name="Colorectal Cancer"
)

# Query: "What is the strongest evidence and why?"
strongest = query.query_strongest_evidence(
    drug_name="Metformin",
    disease_name="Colorectal Cancer",
    top_k=3
)
```

**Query Result Structure:**
```json
{
  "success": true,
  "drug_name": "Metformin",
  "disease_name": "Colorectal Cancer",
  "total_evidence": 5,
  "valid_evidence": 5,
  "evidence": [
    {
      "evidence_id": "uuid",
      "summary": "Phase 3 trial showing 30% reduction...",
      "source_type": "clinical",
      "quality": "high",
      "confidence": 0.9,
      "recency_weight": 0.87,
      "combined_weight": 0.856,
      "agent_name": "Clinical Trials Agent",
      "raw_reference": "NCT12345678"
    }
  ],
  "conflicts": [],
  "has_conflicts": false,
  "explanation": "Found 5 pieces of evidence..."
}
```

---

## Temporal Logic

### Recency Decay

Evidence "freshness" is modeled using **exponential decay** with configurable half-lives:

| Source Type | Half-Life | Rationale |
|-------------|-----------|-----------|
| Clinical | 730 days (2 years) | Clinical trials evolve slowly |
| Patent | 1095 days (3 years) | Patents have long validity |
| Literature | 365 days (1 year) | Literature evolves faster |
| Market | 180 days (6 months) | Market data changes quickly |

**Formula:**
```
recency_weight = 2^(-age_days / half_life)
```

**Example:**
- Clinical trial from 1 year ago (365 days):
  - `weight = 2^(-365/730) = 2^(-0.5) ≈ 0.707`
- Market report from 1 year ago (365 days):
  - `weight = 2^(-365/180) = 2^(-2.03) ≈ 0.245`

### Validity Periods

Evidence can have explicit validity periods:

- **Clinical trials**: Indefinite (unless contradicted)
- **Patents**: 20 years from filing
- **Literature**: Indefinite
- **Market forecasts**: 2 years (then expire)

### Combined Weighting

Final evidence weight combines **three factors**:

1. **Base Quality** (0.5-0.9): Determined by source quality rules
2. **Confidence** (0.0-1.0): From agent's assessment
3. **Recency Weight** (0.1-2.0): Exponential decay

```
combined_weight = (base_quality × confidence × recency_weight) / 2.0
```

This ensures recent, high-quality, high-confidence evidence ranks highest.

---

## Conflict Resolution

### Conflict Types

1. **Efficacy Contradiction**
   - One evidence shows positive results ("effective", "improved")
   - Another shows negative results ("ineffective", "failed")
   - Example: Phase 2 trial succeeds, Phase 3 trial fails

2. **Temporal Invalidation**
   - Newer evidence from later-stage trials supersedes earlier results
   - Example: Phase 3 results invalidate Phase 1 preliminary findings

3. **Source Disagreement**
   - Different source types reach different conclusions
   - Example: Patent claims use for cancer, but clinical trial shows failure

### Conflict Detection Algorithm

```python
# For each pair of evidence (E1, E2):
  if efficacy_contradiction(E1, E2):
    create_conflict(type="efficacy_contradiction", severity=assess_severity(E1, E2))

  if temporal_invalidation(E1, E2):
    create_conflict(type="temporal_invalidation", severity="medium")

  if source_disagreement(E1, E2):
    create_conflict(type="source_disagreement", severity="high")
```

### Conflict Resolution

Conflicts are **NOT automatically resolved**. Instead, AKGP:

1. **Records the conflict** (never deletes evidence)
2. **Ranks evidence** by combined weight
3. **Recommends** which evidence to prefer
4. **Explains** why (quality, confidence, recency)

**Resolution Recommendation Example:**
```
Recommendation: Prefer evidence abc123
Reason: Higher combined weight (0.856 vs 0.623)
Quality: high (vs medium)
Recency: 180 days old (vs 900 days)
Confidence: 0.90 (vs 0.65)
```

---

## Provenance Tracking

### Provenance Chain

Every evidence node has complete lineage:

```
Evidence Node
  ├── agent_name: "Clinical Trials Agent"
  ├── agent_id: "clinical"
  ├── api_source: "ClinicalTrials.gov"
  ├── raw_reference: "NCT12345678"
  ├── extraction_timestamp: 2024-01-15T10:30:00Z
  ├── source_type: "clinical"
  ├── quality: "high"
  └── confidence_score: 0.85
```

### Audit Trail

Provenance tracker maintains an audit log:

```python
audit_report = tracker.generate_audit_report()

# Returns:
{
  "total_evidence": 150,
  "evidence_by_agent": {
    "Clinical Trials Agent": 80,
    "Patent Intelligence Agent": 50,
    "Market Intelligence Agent": 20
  },
  "evidence_by_source_type": {
    "clinical": 80,
    "patent": 50,
    "market": 20
  },
  "evidence_by_quality": {
    "high": 60,
    "medium": 70,
    "low": 20
  },
  "average_confidence_by_agent": {
    "Clinical Trials Agent": 0.82,
    "Patent Intelligence Agent": 0.68,
    "Market Intelligence Agent": 0.55
  }
}
```

### Source Quality Assessment

Deterministic rules assign quality levels:

**Clinical Trials:**
- **HIGH**: Phase 3/4, completed trials
- **MEDIUM**: Phase 2, recruiting trials
- **LOW**: Phase 1, early-stage trials

**Patents:**
- **HIGH**: Granted patents (US######)
- **MEDIUM**: Published applications
- **LOW**: Patent searches

**Market Intelligence:**
- **HIGH**: Tier 1 sources (IQVIA, EvaluatePharma)
- **MEDIUM**: Industry reports
- **LOW**: Web sources, news articles

---

## Usage Examples

### Example 1: Ingest Clinical Trial

```python
from akgp.graph_manager import GraphManager
from akgp.ingestion import IngestionEngine

# Initialize
graph = GraphManager(use_in_memory=True)
ingestion = IngestionEngine(graph)

# Ingest clinical trial from agent
trial_data = {
    "nct_id": "NCT04098549",
    "title": "Metformin for Colorectal Cancer Prevention",
    "summary": "Phase 3 randomized trial showing 30% reduction in polyp recurrence",
    "interventions": ["Metformin"],
    "conditions": ["Colorectal Cancer"],
    "phase": "Phase 3",
    "status": "Completed",
    "confidence_score": 0.88
}

result = ingestion.ingest_clinical_trial(trial_data)
print(f"Created {len(result['created_nodes'])} nodes, {len(result['created_relationships'])} relationships")
```

### Example 2: Query Evidence

```python
from akgp.query_engine import QueryEngine

query = QueryEngine(graph)

# Query evidence
result = query.query_drug_disease_evidence(
    drug_name="Metformin",
    disease_name="Colorectal Cancer"
)

print(result['explanation'])
print(f"Total evidence: {result['total_evidence']}")
print(f"Strongest: {result['strongest_evidence']['agent_name']} (weight: {result['strongest_evidence']['combined_weight']:.3f})")

# Check for conflicts
if result['has_conflicts']:
    print(f"⚠️  Warning: {len(result['conflicts'])} conflict(s) detected")
```

### Example 3: Detect Conflicts

```python
from akgp.conflict_resolution import ConflictDetector

detector = ConflictDetector()

# Get all evidence for Metformin → Cancer
# (from previous query)
evidence_list = [...]

# Detect conflicts
conflicts = detector.detect_conflicts(evidence_list)

for conflict in conflicts:
    print(f"Conflict: {conflict.conflict_type}")
    print(f"Severity: {conflict.severity}")
    print(f"Explanation: {conflict.explanation}")

    # Get resolution recommendation
    resolution = detector.resolve_conflict(conflict, evidence1, evidence2)
    print(f"Recommendation: {resolution['explanation']}")
```

---

## How AKGP Differs from Static Knowledge Graphs

| Feature | Static KG | AKGP |
|---------|-----------|------|
| **Temporal Reasoning** | ❌ No concept of time | ✅ Recency weighting, validity periods |
| **Conflict Handling** | ❌ Overwrites conflicting data | ✅ Records all conflicts, ranks evidence |
| **Provenance** | ⚠️ Optional, incomplete | ✅ Mandatory, complete audit trails |
| **Evidence Quality** | ⚠️ Binary (present/absent) | ✅ Multi-level (high/medium/low) + confidence |
| **Explainability** | ❌ Black-box queries | ✅ Detailed explanations for all results |
| **Adaptability** | ❌ Static snapshot | ✅ Adapts as new evidence arrives |
| **Multi-Agent** | ❌ Single source | ✅ Integrates evidence from multiple agents |
| **Regulatory Compliance** | ⚠️ Limited | ✅ Full audit trails, provenance chains |

---

## Research Contribution

AKGP represents a novel approach to pharmaceutical knowledge graphs:

### 1. **Temporal Adaptivity**
- First system to apply exponential decay weighting to biomedical evidence
- Configurable half-lives per evidence type
- Validity periods for time-sensitive data (market forecasts)

### 2. **Conflict-Aware Evidence Aggregation**
- Deterministic conflict detection (3 rule types)
- Weight-based resolution recommendations
- Records all conflicts (never overwrites)

### 3. **Multi-Agent Evidence Integration**
- Structured ingestion from clinical, patent, and market agents
- Unified representation across heterogeneous sources
- Agent-agnostic schema

### 4. **Explainable Drug Repurposing**
- All weights and scores are deterministic
- Query results include detailed explanations
- Traceable provenance for all evidence

### 5. **Regulatory-Ready Architecture**
- Complete audit trails
- Provenance chains for all evidence
- Quality assessment rules
- Reproducible results

---

## Future Extensions

### Planned Features

1. **Neo4j Cypher Query Interface** - Direct graph queries
2. **UMLS Integration** - Automatic drug/disease normalization
3. **Evidence Expiration Jobs** - Automatic validity end enforcement
4. **Conflict Resolution UI** - Visual conflict review and resolution
5. **Literature Agent Integration** - PubMed evidence ingestion
6. **GraphQL API** - Modern query interface

### Research Directions

1. **Learned Recency Functions** - Replace exponential decay with learned curves
2. **Automatic Conflict Resolution** - ML-based resolution (with explanations)
3. **Federated Knowledge Graphs** - Merge multiple AKGP instances
4. **Uncertainty Quantification** - Bayesian confidence intervals

---

## Citation

If you use AKGP in your research, please cite:

```bibtex
@software{akgp2024,
  title = {AKGP: Adaptive Knowledge Graph Protocol for Drug Repurposing},
  author = {MAESTRO Team},
  year = {2024},
  version = {1.0.0},
  url = {https://github.com/dhruvd-1/MAESTRO}
}
```

---

## License

Copyright © 2024 MAESTRO Team. All rights reserved.

---

**END OF README**
