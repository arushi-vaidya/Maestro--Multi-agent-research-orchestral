# API FAÇADE LAYER - STEP 7.6

## Overview

The API Façade Layer is a **thin, READ-ONLY presentation boundary** between the MAESTRO backend intelligence stack and the frontend UI.

**Purpose**: Provide a stable, frontend-safe API surface that exposes already-computed data in a clean format, without triggering any backend computation.

**Key Principle**: This layer **NEVER** modifies data, triggers agents, or recomputes results. It only exposes what has already been computed.

---

## Architecture

```
Frontend Pages
     ↓
API Façade Layer (READ-ONLY)
     ↓
Query Result Cache
     ↓
Backend Intelligence Stack
  - Master Agent
  - Specialized Agents (Clinical, Patent, Market, Literature)
  - AKGP Knowledge Graph
  - ROS Engine
  - Conflict Reasoning
```

**Flow**:
1. User submits query via `POST /api/query`
2. Backend processes query (agents → AKGP → ROS → conflict reasoning)
3. Results are cached in `QueryResultCache`
4. Frontend reads cached results via façade endpoints
5. Façade endpoints return frontend-safe, stable response schemas

---

## Critical Constraints

### ✅ ALLOWED
- Add new API endpoints
- Add response models (Pydantic schemas)
- Add serialization/adaptation logic
- Read from cache
- Read from AKGP (read-only queries)
- Add API documentation

### ❌ FORBIDDEN
- Modify frozen components:
  - `agents/**`
  - `normalization/**`
  - `akgp/**`
  - `ros/**`
  - `graph_orchestration/**`
- Trigger agent execution
- Modify AKGP graph
- Recompute ROS scores
- Bypass existing validation
- Break existing tests

---

## Endpoints

### Core Endpoint

#### `POST /api/query`
**Purpose**: Main query processing endpoint (existing, enhanced with cache population)

**Request**:
```json
{
  "query": "Analyze semaglutide for Alzheimer's disease"
}
```

**Response**: `QueryResponse` (full response with all data)

**Side Effect** (STEP 7.6): Populates `QueryResultCache` for façade views

---

### Façade Endpoints (NEW - STEP 7.6)

All façade endpoints are **READ-ONLY** and return already-computed data.

---

#### 1. `GET /api/ros/latest`
**Purpose**: Get ROS score for last queried drug-disease pair

**Response Schema**: `ROSViewResponse`
```json
{
  "drug": "Semaglutide",
  "disease": "Alzheimer's Disease",
  "ros_score": 5.2,
  "confidence_level": "MEDIUM",
  "breakdown": {
    "evidence_strength": 2.8,
    "evidence_diversity": 1.5,
    "conflict_penalty": -1.2,
    "recency_boost": 1.1,
    "patent_risk_penalty": -0.5
  },
  "conflict_penalty": -1.2,
  "explanation": "Moderate evidence strength from 3 agents. Significant conflict detected between clinical and literature evidence. Recent studies (2024) show mixed results.",
  "metadata": {
    "computation_timestamp": "2025-01-19T12:00:00Z",
    "num_supporting_evidence": 8,
    "num_contradicting_evidence": 4,
    "distinct_agents": ["clinical", "literature", "market"]
  }
}
```

**Frontend Page**: Page 1 (Prompt & ROS Results)

**Data Source**: Cache (from last `POST /api/query`)

**Error Codes**:
- `404`: No ROS results available (execute query first)
- `500`: Error reading cache

---

#### 2. `GET /api/graph/summary`
**Purpose**: Get knowledge graph nodes and edges for visualization

**Query Parameters**:
- `node_limit` (int, default=100): Maximum nodes to return
- `include_evidence` (bool, default=false): Include evidence nodes

**Response Schema**: `GraphSummaryResponse`
```json
{
  "nodes": [
    {
      "id": "drug_abc123",
      "label": "Semaglutide",
      "type": "drug",
      "metadata": {
        "drug_class": "GLP-1 agonist",
        "synonyms": ["Ozempic", "Wegovy"]
      }
    },
    {
      "id": "disease_xyz789",
      "label": "Alzheimer's Disease",
      "type": "disease",
      "metadata": {
        "disease_category": "Neurodegenerative"
      }
    }
  ],
  "edges": [
    {
      "source": "drug_abc123",
      "target": "disease_xyz789",
      "relationship": "INVESTIGATED_FOR",
      "weight": 0.75,
      "metadata": {
        "evidence_id": "ev_111",
        "agent_id": "clinical"
      }
    }
  ],
  "statistics": {
    "total_nodes": 2,
    "total_edges": 1,
    "node_counts": {
      "drug": 1,
      "disease": 1
    },
    "graph_mode": "in_memory"
  }
}
```

**Frontend Page**: Page 2 (Knowledge Graph Explorer)

**Data Source**: AKGP GraphManager (read-only queries)

**Node Types**:
- `drug`: Drug/compound nodes
- `disease`: Disease/indication nodes
- `evidence`: Evidence nodes (if `include_evidence=true`)
- `trial`: Clinical trial nodes
- `patent`: Patent nodes
- `market_signal`: Market intelligence nodes

**Relationship Types**:
- `TREATS`: Established treatment relationship
- `INVESTIGATED_FOR`: Under investigation
- `SUGGESTS`: Evidence suggests relationship
- `CONTRADICTS`: Conflicting evidence
- `SUPPORTS`: Corroborating evidence

---

#### 3. `GET /api/evidence/timeline`
**Purpose**: Get chronologically sorted evidence for timeline visualization

**Query Parameters**:
- `limit` (int, default=100): Maximum events to return
- `agent_filter` (str, optional): Filter by agent (e.g., 'clinical')
- `quality_filter` (str, optional): Filter by quality ('LOW', 'MEDIUM', 'HIGH')

**Response Schema**: `EvidenceTimelineResponse`
```json
{
  "events": [
    {
      "timestamp": "2024-03-15T10:30:00Z",
      "source": "ClinicalTrials.gov",
      "polarity": "SUPPORTS",
      "confidence": 0.85,
      "quality": "HIGH",
      "reference_id": "NCT05123456",
      "summary": "Phase 3 trial showing 12% reduction in cognitive decline",
      "agent_id": "clinical",
      "recency_weight": 0.92
    },
    {
      "timestamp": "2024-01-20T08:15:00Z",
      "source": "PubMed",
      "polarity": "CONTRADICTS",
      "confidence": 0.65,
      "quality": "MEDIUM",
      "reference_id": "PMID: 38123456",
      "summary": "Meta-analysis finds no significant cognitive benefit",
      "agent_id": "literature",
      "recency_weight": 0.88
    }
  ],
  "total_count": 2,
  "date_range": {
    "earliest": "2024-01-20T08:15:00Z",
    "latest": "2024-03-15T10:30:00Z"
  },
  "agent_distribution": {
    "clinical": 1,
    "literature": 1
  },
  "polarity_distribution": {
    "SUPPORTS": 1,
    "CONTRADICTS": 1
  }
}
```

**Frontend Page**: Page 3 (Evidence Timeline)

**Data Source**: AKGP GraphManager (evidence nodes, read-only)

**Polarity Values**:
- `SUPPORTS`: Strong positive evidence
- `SUGGESTS`: Weak/speculative evidence
- `CONTRADICTS`: Negative evidence

**Quality Values**:
- `HIGH`: Phase 3/4 trials, granted patents, peer-reviewed papers
- `MEDIUM`: Phase 2 trials, patent applications, market reports
- `LOW`: Phase 1 trials, patent searches, web sources

---

#### 4. `GET /api/conflicts/explanation`
**Purpose**: Get conflict explanation for last query

**Response Schema**: `ConflictExplanationResponse`
```json
{
  "has_conflict": true,
  "severity": "MEDIUM",
  "dominant_evidence_id": "ev_12345",
  "explanation": "Moderate conflict detected: 8 evidence pieces support the hypothesis, but 3 recent studies contradict. Newer evidence (Phase 3 trial NCT05123456) shows lower efficacy than earlier Phase 2 results.",
  "supporting_evidence": [
    {
      "evidence_id": "ev_11111",
      "source": "ClinicalTrials.gov",
      "agent_id": "clinical",
      "quality": "HIGH",
      "confidence": 0.9,
      "reference": "NCT05123456"
    }
  ],
  "contradicting_evidence": [
    {
      "evidence_id": "ev_22222",
      "source": "PubMed",
      "agent_id": "literature",
      "quality": "MEDIUM",
      "confidence": 0.7,
      "reference": "PMID: 34567890"
    }
  ],
  "temporal_reasoning": "Recent Phase 3 trial (2024) contradicts earlier Phase 2 results (2022)",
  "evidence_counts": {
    "supports": 8,
    "contradicts": 3,
    "suggests": 5
  }
}
```

**Frontend Page**: Page 4 (Conflict & Explanation)

**Data Source**: Cache (from `ros_results.conflict_summary` in last query)

**Severity Levels**:
- `NONE`: No conflicts detected
- `LOW`: Weak evidence conflicts (low confidence)
- `MEDIUM`: Moderate conflicts (mixed confidence)
- `HIGH`: Strong evidence conflicts (high confidence disagreement)

---

#### 5. `GET /api/execution/status`
**Purpose**: Get execution status and timing for last query

**Response Schema**: `ExecutionStatusResponse`
```json
{
  "agents_triggered": ["clinical", "market", "patent", "literature"],
  "agents_completed": ["clinical", "market", "patent", "literature"],
  "agents_failed": [],
  "agent_details": [
    {
      "agent_id": "clinical",
      "status": "completed",
      "started_at": "2024-01-19T10:00:00Z",
      "completed_at": "2024-01-19T10:00:05Z",
      "duration_ms": 5000,
      "result_count": 45,
      "error": null
    },
    {
      "agent_id": "market",
      "status": "completed",
      "started_at": "2024-01-19T10:00:00Z",
      "completed_at": "2024-01-19T10:00:08Z",
      "duration_ms": 8000,
      "result_count": 28,
      "error": null
    }
  ],
  "ingestion_summary": {
    "total_evidence": 120,
    "ingested_evidence": 115,
    "rejected_evidence": 5
  },
  "execution_time_ms": 13000,
  "query_timestamp": "2024-01-19T10:00:00Z",
  "metadata": {
    "orchestration_mode": "langgraph_parallel",
    "classification_timestamp": "2024-01-19T10:00:00.123Z",
    "join_timestamp": "2024-01-19T10:00:10.456Z",
    "joined_agents": ["clinical", "market", "patent", "literature"]
  }
}
```

**Frontend Page**: Page 5 (Confidence/ROS Breakdown), Page 1 (execution status indicators)

**Data Source**: Cache (from `execution_metadata` and `agent_execution_status` in last query)

**Agent Status Values**:
- `completed`: Agent finished successfully
- `running`: Agent currently executing
- `failed`: Agent encountered error

**Orchestration Modes**:
- `sequential`: Sequential agent execution (legacy)
- `langgraph_parallel`: Parallel execution via LangGraph (STEP 7 Phase 2)

---

## Frontend Page Mapping

| Frontend Page | Primary Endpoint | Secondary Endpoints |
|---------------|------------------|---------------------|
| **1. Prompt & ROS Results** | `GET /api/ros/latest` | `GET /api/execution/status` |
| **2. Knowledge Graph Explorer** | `GET /api/graph/summary` | - |
| **3. Evidence Timeline** | `GET /api/evidence/timeline` | - |
| **4. Conflict & Explanation** | `GET /api/conflicts/explanation` | - |
| **5. Confidence/ROS Breakdown** | `GET /api/ros/latest`, `GET /api/execution/status` | - |

---

## Stability Guarantee

**Frontend Contract**:
- All response schemas are **versioned** and **stable**
- Additive changes only (no breaking changes)
- Deprecated fields will be marked but not removed
- New fields will be optional

**Backend Evolution**:
- Backend intelligence stack can evolve independently
- Façade layer adapts backend changes to stable frontend schemas
- Frontend code does not need updates unless new features are desired

---

## Cache Behavior

### Query Result Cache

**Purpose**: Store results from last `POST /api/query` execution

**Storage**: In-memory (thread-safe singleton)

**Lifetime**: Until next query executes (overwrites cache)

**Contents**:
- Last query string
- Full `QueryResponse` object
- ROS computation result
- AKGP query result (optional)
- Execution metadata
- Drug/disease IDs (if detected)

**Concurrency**: Thread-safe with locks

**Eviction**: No TTL - only overwrites on new query

---

## Error Handling

### Standard Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `200` | Success | Display data |
| `404` | No data available | Prompt user to execute query first |
| `500` | Server error | Display error message, retry |

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

---

## Testing

### Test Coverage

All façade endpoints have comprehensive tests covering:
1. **Schema validation**: Responses match Pydantic models
2. **Idempotency**: Multiple calls return same data
3. **Read-only**: No agents triggered, no graph modifications
4. **Regression**: Existing tests still pass

### Test Location

`backend/tests/api_views/`

### Running Tests

```bash
cd backend
pytest tests/api_views/ -v
```

---

## Implementation Details

### Directory Structure

```
backend/api/
├── routes.py               # Main router + query endpoint (modified)
└── views/
    ├── __init__.py        # Cache export
    ├── cache.py           # QueryResultCache singleton
    ├── ros_view.py        # ROS façade endpoint
    ├── graph_view.py      # Graph façade endpoint
    ├── evidence_view.py   # Evidence façade endpoint
    ├── conflict_view.py   # Conflict façade endpoint
    └── execution_view.py  # Execution façade endpoint
```

### Modified Files

**`backend/api/routes.py`**:
- Added imports for all view routers
- Included view routers in main router
- Modified `POST /api/query` to populate cache

**No other files modified** (frozen components untouched)

---

## Usage Examples

### Typical Frontend Flow

1. **User submits query**:
   ```javascript
   const response = await fetch('/api/query', {
     method: 'POST',
     body: JSON.stringify({ query: userInput })
   });
   const data = await response.json();
   ```

2. **Frontend navigates to ROS page**:
   ```javascript
   const rosData = await fetch('/api/ros/latest').then(r => r.json());
   // Display ROS score visualization
   ```

3. **Frontend shows knowledge graph**:
   ```javascript
   const graphData = await fetch('/api/graph/summary?include_evidence=false')
     .then(r => r.json());
   // Render D3.js/Three.js graph
   ```

4. **Frontend shows evidence timeline**:
   ```javascript
   const timeline = await fetch('/api/evidence/timeline?limit=50')
     .then(r => r.json());
   // Render chronological timeline
   ```

5. **Frontend shows conflict explanation**:
   ```javascript
   const conflicts = await fetch('/api/conflicts/explanation')
     .then(r => r.json());
   // Display conflict reasoning
   ```

6. **Frontend shows execution status**:
   ```javascript
   const execution = await fetch('/api/execution/status')
     .then(r => r.json());
   // Show agent timing and status
   ```

---

## Design Rationale

### Why a Façade Layer?

1. **Separation of Concerns**: Frontend doesn't need to understand backend internals
2. **Stability**: Backend can evolve without breaking frontend
3. **Type Safety**: Pydantic models ensure consistent schemas
4. **Performance**: Read-only caching avoids redundant computation
5. **Testability**: Façade endpoints can be tested independently

### Why Caching?

1. **Avoid Recomputation**: ROS/conflict/AKGP queries are expensive
2. **Consistent Data**: All façade views see same query results
3. **Fast Response**: Frontend gets instant responses

### Why Read-Only?

1. **Safety**: Prevents accidental data corruption
2. **Predictability**: No side effects from GET requests
3. **Idempotency**: Multiple calls safe and consistent
4. **RESTful**: Follows REST principles (GET = read-only)

---

## Future Enhancements (Out of Scope for STEP 7.6)

Potential future improvements:
- WebSocket endpoint for real-time agent status streaming
- Query history API (`GET /api/queries/history`)
- Export endpoints (`GET /api/export/pdf`, `GET /api/export/json`)
- User preferences API
- Persistent cache with TTL
- Multi-query comparison endpoint

**Note**: These are NOT part of STEP 7.6. This step is strictly READ-ONLY façade for existing data.

---

## Verification Checklist

✅ All façade endpoints return schema-valid responses
✅ No agents triggered by façade endpoints
✅ No graph modifications from façade endpoints
✅ Idempotent: multiple calls return same data
✅ All existing tests pass (no regression)
✅ No frozen modules modified
✅ Documentation complete
✅ Tests written and passing

---

## Summary

The API Façade Layer (STEP 7.6) provides a **thin, READ-ONLY, stable presentation boundary** for the frontend, exposing already-computed backend intelligence in a clean, frontend-safe format.

**Core Principle**: **READ-ONLY** - No computation, no modification, no side effects.

**Result**: Frontend can build all 5 pages using stable, well-typed APIs without touching backend internals.
