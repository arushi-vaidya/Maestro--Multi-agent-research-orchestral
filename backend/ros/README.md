# Research Opportunity Scoring (ROS) - Phase 6A

## Overview

**Research Opportunity Scoring (ROS)** is a deterministic, explainable, heuristic system for ranking drug-disease pairs based on evidence from the AKGP knowledge graph.

**Phase 6A** (this implementation): Heuristic ROS with explicit rules (NO ML)
**Phase 6B** (future): ML-enhanced ROS with learned weights

---

## Mathematical Formulation

### Final Score Formula

```
ROS_score = CLAMP(
    evidence_strength +
    evidence_diversity +
    conflict_penalty +
    recency_boost +
    patent_risk_penalty,
    min=0.0,
    max=10.0
)
```

**Range**: [0.0, 10.0]

---

## Feature Definitions

### 1. Evidence Strength (0-4 points)

**Purpose**: Quantify the total weight of supporting evidence

**Formula**:
```
evidence_strength = MAX_STRENGTH × log(1 + Σ(quality_weight × confidence)) / log(11)

where:
- quality_weight(HIGH) = 1.0
- quality_weight(MEDIUM) = 0.6
- quality_weight(LOW) = 0.3
- confidence ∈ [0.0, 1.0]
- MAX_STRENGTH = 4.0
```

**Rationale**:
- **Quality weighting**: High-quality evidence (Phase 3 trials, granted patents) carries more weight than low-quality evidence (Phase 1 trials, patent searches)
- **Confidence scaling**: Agent confidence scores modulate evidence contribution
- **Logarithmic normalization**: Prevents unbounded growth; log(1+x) ensures diminishing returns for very large evidence sets
- **SUPPORTS + SUGGESTS**: Both contribute to evidence strength (SUGGESTS is weak support)

**Example**:
- 1 HIGH-quality evidence (conf=0.9): `4.0 × log(1.9) / log(11) ≈ 1.1 points`
- 3 MEDIUM-quality evidence (conf=0.7 each): `4.0 × log(2.26) / log(11) ≈ 1.4 points`

---

### 2. Evidence Diversity (0-2 points)

**Purpose**: Reward multi-source corroboration

**Formula**:
```
evidence_diversity = diversity_score(num_distinct_agents)

where:
- 1 agent  = 0.5 points
- 2 agents = 1.0 points
- 3 agents = 1.5 points
- 4+ agents = 2.0 points
```

**Rationale**:
- **Single-source bias**: Evidence from one agent may have blind spots
- **Corroboration**: Multiple independent agents increase confidence
- **Complementary strengths**:
  - Clinical: Efficacy/safety data
  - Patent: IP landscape
  - Market: Commercial viability
  - Literature: Scientific foundation

**Example**:
- Only clinical evidence: 0.5 points
- Clinical + market evidence: 1.0 points
- Clinical + market + patent + literature: 2.0 points

---

### 3. Conflict Penalty (0 to -3 points)

**Purpose**: Penalize conflicting evidence (uncertainty indicator)

**Formula**:
```
conflict_penalty = penalty(conflict_severity)

where:
- HIGH conflict   = -3.0 points  (strong evidence on both sides)
- MEDIUM conflict = -1.5 points  (asymmetric evidence quality)
- LOW conflict    = -0.5 points  (weak evidence conflict)
- NO conflict     =  0.0 points
```

**Rationale**:
- **HIGH conflict**: Multiple high-quality sources disagree → major research risk
  - Example: Phase 3 trial shows efficacy, but another Phase 3 shows failure
- **MEDIUM conflict**: Quality asymmetry → moderate uncertainty
  - Example: Phase 3 shows efficacy, but Phase 1 shows toxicity
- **LOW conflict**: Weak evidence disagrees → minor noise
  - Example: Preclinical data conflicts, not definitive
- **Harsh penalties**: Conflicts indicate high research/development risk

**Example**:
- No conflicts: 0.0 penalty
- LOW conflict (Phase 1 vs preclinical): -0.5 penalty
- HIGH conflict (Phase 3 vs Phase 3): -3.0 penalty

---

### 4. Recency Boost (0-2 points)

**Purpose**: Reward recent evidence (indicates active research)

**Formula**:
```
recency_boost = MAX_BOOST × avg(temporal_weight)

where:
- temporal_weight = AKGP temporal decay function
- Uses half-life decay:
  - Clinical: 2 years
  - Patent: 3 years
  - Literature: 1 year
  - Market: 6 months
- MIN_WEIGHT = 0.1 (even old evidence has value)
- MAX_BOOST = 2.0
```

**Rationale**:
- **Active research**: Recent evidence indicates ongoing development
- **Temporal decay**: Different source types age differently
  - Market data expires quickly (6 months)
  - Clinical trials age slowly (2 years)
  - Patents have long validity (3 years)
- **Old evidence still valid**: Minimum weight of 0.1 prevents complete discounting

**Example**:
- All evidence from 2024: avg_weight ≈ 1.0 → 2.0 boost
- All evidence from 2020: avg_weight ≈ 0.5 → 1.0 boost
- All evidence from 2015: avg_weight ≈ 0.2 → 0.4 boost

---

### 5. Patent Risk Penalty (0 to -2 points)

**Purpose**: Penalize high patent activity (FTO risk)

**Formula**:
```
patent_risk_penalty = penalty(active_patent_count)

where:
- Many (>10 active patents) = -2.0 points
- Some (3-10 active)        = -1.0 points
- Few (1-2 active)          = -0.3 points
- None (0 active)           =  0.0 points

active = unexpired patents only
```

**Rationale**:
- **Freedom-to-Operate (FTO)**: Many active patents indicate IP barriers
  - Costly licensing or litigation risk
  - Development may be blocked
- **Strategic risk**: High patent density reduces commercial viability
- **Expired patents**: No penalty (clear IP landscape)
- **No patents**: No penalty, but also indicates less commercial validation

**Example**:
- 15 active patents (crowded IP landscape): -2.0 penalty
- 5 active patents (moderate IP risk): -1.0 penalty
- 1 expired patent: 0.0 penalty

---

## Score Interpretation

| ROS Score | Interpretation | Recommendation |
|-----------|----------------|----------------|
| **8.0-10.0** | **Exceptional** | High-priority research opportunity |
| **6.0-7.9** | **Strong** | Promising opportunity, worth pursuing |
| **4.0-5.9** | **Moderate** | Viable but cautious approach needed |
| **2.0-3.9** | **Weak** | High risk, requires further validation |
| **0.0-1.9** | **Poor** | Not recommended without new evidence |

---

## Design Rationale

### Why Heuristic ROS Before ML ROS?

**Phase 6A (Heuristic) serves as:**
1. **Baseline**: ML models in Phase 6B will be compared against this
2. **Interpretability**: Fully explainable for regulatory/journal submission
3. **Transparency**: No black-box decisions
4. **Auditability**: Every score component traceable to AKGP data
5. **Robustness**: Works with small datasets (ML needs large training sets)

**Phase 6B (ML) will add:**
- Learned feature weights (not hardcoded)
- Non-linear feature interactions
- Adaptive scoring based on domain/indication
- Uncertainty quantification

---

## Key Properties

### 1. Determinism
**Same inputs → same outputs**
- No randomness
- No ML model stochasticity
- No time-dependent side effects

### 2. Monotonicity
- More SUPPORTS evidence → higher score
- More conflicts → lower score
- Newer evidence → higher score
- More patent barriers → lower score

### 3. Explainability
Every score component has:
- Clear mathematical formula
- Human-readable justification
- Traceable to AKGP evidence

### 4. Auditability
- All weights defined in `scoring_rules.py`
- All extractors in `feature_extractors.py`
- Full provenance trail to evidence sources

---

## Data Flow

```
Drug-Disease Pair
    ↓
AKGP Query Engine (FROZEN - STEP 4)
    ↓
Conflict Reasoning (FROZEN - STEP 5)
    ↓
    ├─→ Evidence Strength Extractor
    ├─→ Evidence Diversity Extractor
    ├─→ Conflict Penalty Extractor
    ├─→ Recency Boost Extractor (uses AKGP Temporal Reasoner)
    └─→ Patent Risk Extractor
    ↓
Feature Aggregation
    ↓
ROS Score (0-10) + Explanation
```

**CRITICAL**: ROS uses ONLY AKGP outputs (never raw agent data)

---

## Usage Example

```python
from ros import compute_ros
from akgp.graph_manager import GraphManager
from akgp.conflict_reasoning import ConflictReasoner

# Initialize AKGP components (from STEPS 1-5)
graph = GraphManager()
conflict_reasoner = ConflictReasoner(graph)

# Compute ROS
result = compute_ros(
    drug_id="canonical_drug_12345",
    disease_id="canonical_disease_67890",
    graph_manager=graph,
    conflict_reasoner=conflict_reasoner
)

print(result['ros_score'])  # e.g., 7.2
print(result['explanation'])
print(result['feature_breakdown'])
```

**Output**:
```json
{
  "drug_id": "canonical_drug_12345",
  "disease_id": "canonical_disease_67890",
  "ros_score": 7.2,
  "feature_breakdown": {
    "evidence_strength": 3.1,
    "evidence_diversity": 1.5,
    "conflict_penalty": -0.5,
    "recency_boost": 1.8,
    "patent_risk_penalty": -1.0
  },
  "conflict_summary": {
    "has_conflict": true,
    "severity": "LOW",
    "dominant_evidence": "SUPPORTS"
  },
  "explanation": "Research Opportunity Score: 7.2/10.0 Evidence Strength (3.1/4.0): 4 supporting + 2 suggesting evidence sources. Evidence Diversity (1.5/2.0): Evidence from 3 distinct agent source(s). Conflict Penalty (-0.5): LOW severity conflict detected between evidence sources. Recency Boost (1.8/2.0): Recent evidence indicates active research area. Patent Risk Penalty (-1.0): 5 patent(s) detected, indicating IP complexity."
}
```

---

## Validation Tests

See `tests/integration/ros/` for comprehensive test suite:
- `test_ros_basic_scoring.py`: Core scoring logic
- `test_ros_conflict_penalty.py`: Conflict sensitivity
- `test_ros_temporal_sensitivity.py`: Recency weighting
- `test_ros_monotonicity.py`: Monotonicity guarantees
- `test_ros_explanations.py`: Explanation correctness

---

## Freeze Conditions

**STEP 6A is COMPLETE when:**
- ✅ All ROS tests pass
- ✅ All existing tests still pass (no regressions)
- ✅ ROS uses only AKGP + conflict reasoning
- ✅ No ML code exists
- ✅ No frozen files modified (STEPS 0-5)
- ✅ README documents math clearly

**After freeze:**
- STEP 6A code is FROZEN
- Phase 6B (ML ROS) is deferred to future work

---

## Future Work (Phase 6B)

**ML-Enhanced ROS** will add:
1. **Learned Weights**: Train feature weights on historical success data
2. **Feature Engineering**: Discover non-linear feature interactions
3. **Domain Adaptation**: Per-indication scoring models
4. **Uncertainty Quantification**: Confidence intervals for scores
5. **Active Learning**: Update model as new evidence arrives

**NOT in Phase 6A**: No ML, no training, no model weights

---

## References

- **AKGP Schema**: `backend/akgp/schema.py`
- **Conflict Reasoning**: `backend/akgp/conflict_reasoning.py` (STEP 5)
- **Temporal Logic**: `backend/akgp/temporal.py`
- **Scoring Rules**: `backend/ros/scoring_rules.py`
- **Feature Extractors**: `backend/ros/feature_extractors.py`
- **ROS Engine**: `backend/ros/ros_engine.py`

---

**Author**: Maestro PharmaGraph Team
**Version**: 1.0.0-phase6a
**Date**: 2026-01-19
**Status**: STEP 6A Implementation
