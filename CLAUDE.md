# Claude Playbook

## Overview
- Purpose: notes and conventions for Claude interactions within this repo.
- Scope: prompting guidelines, safety reminders, and runbook references.

## Prompting Tips
- State objective, constraints, and expected format up front.
- Prefer short system prompts; keep examples minimal and focused.
- Call out any privacy or safety requirements explicitly.

## Runbook
- Link tasks to issue IDs and include acceptance criteria.
- Log assumptions and edge cases before running agents.
- Capture failures with inputs, outputs, and repro steps.

## Troubleshooting npm install
- Verify Node version: `node -v` (match project `.nvmrc` or docs).
- Clear npm cache: `npm cache clean --force`.
- Remove lock/artifacts: delete `node_modules/`, `package-lock.json`, then `npm install`.
- Check registry/auth: `npm config get registry`; ensure VPN/token if using private scope.
- Inspect verbose logs: `npm install --verbose` and review the first error.
- Rebuild native deps: `npm rebuild` or install build tools (Xcode CLT/Build-Essentials).
- Proxy/SSL issues: set `npm config set strict-ssl false` temporarily if needed; prefer fixing certs.
- Disk/permissions: ensure write access; on *nix avoid sudo, fix with `chown -R $(whoami) .`.

## Troubleshooting Backend Crashes

### "Failed to connect to backend" Error

**Symptoms**:
- Frontend shows "Failed to connect to backend"
- Browser console: "TypeError: Load failed"
- Backend terminal: No active process or crash logs

**Common Causes**:
1. **Missing API Keys**: GROQ_API_KEY or GOOGLE_API_KEY not set
2. **SERPAPI_KEY Missing**: Market Agent crashes without graceful fallback
3. **Port Conflict**: Another process using port 8000
4. **Import Errors**: Missing Python dependencies

**Fix Steps**:

```bash
# 1. Check if backend is running
lsof -i :8000
# If nothing shown, backend crashed or not started

# 2. Verify environment variables
cd backend
cat .env
# Should contain: GROQ_API_KEY, GOOGLE_API_KEY, SERPAPI_KEY (optional)

# 3. If .env missing, create from template
cp .env.example .env
# Edit .env and add your API keys

# 4. Restart backend with verbose logging
python main.py
# Watch for startup diagnostics

# 5. Test backend health
curl http://localhost:8000/api/agents/status
```

**Quick Fix for SERPAPI_KEY Missing**:
```bash
# Backend will work without SERPAPI_KEY (uses RAG only)
# But you'll see warning: "Market Agent will return limited results"
# To fix: Get free key from https://serpapi.com/users/sign_up
export SERPAPI_KEY=your_key_here
python main.py
```

**API Key Sources**:
- **GROQ**: https://console.groq.com/keys (free tier available)
- **Gemini**: https://aistudio.google.com/app/apikey (free tier available)
- **SerpAPI**: https://serpapi.com/users/sign_up (100 free searches/month)

### Backend Won't Start

```bash
# Check Python dependencies
cd backend
pip install -r requirements.txt

# Check for import errors
python -c "from agents.master_agent import MasterAgent; print('✅ OK')"

# If fails, check specific module
python -c "from utils.web_search import WebSearchEngine; print('✅ OK')"
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000
# Kill it: kill -9 <PID>

# Or use different port
cd backend
# Edit main.py: uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Frontend Can't Reach Backend

```bash
# Verify backend URL in frontend
cd frontend
cat .env
# Should contain: REACT_APP_API_URL=http://localhost:8000

# Test backend from command line
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

## Maestro Architecture Analysis

### System Overview
**Project**: Multi-Agent Research Orchestral (Maestro)
**Stack**: Python FastAPI backend + React TypeScript frontend
**Purpose**: Pharmaceutical intelligence aggregation using specialized AI agents

### Backend Architecture (`/backend`)

#### 1. Master Agent (`agents/master_agent.py`)
**Role**: Query orchestrator and intelligent agent router

**Query Classification Logic**:
- **Multi-dimensional**: FTO, patent landscape, due diligence → BOTH agents
- **Market only**: market size, CAGR, revenue, forecast → Market agent
- **Clinical only**: trials, efficacy, safety, NCT IDs → Clinical agent
- **Default**: Run both agents for comprehensive coverage

**Execution Flow**:
```
User Query → Classification → Agent Routing → Parallel Execution → Result Fusion → Response
```

**Key Methods**:
- `_classify_query()`: Determines which agents to activate (market, clinical, or both)
- `_run_clinical_agent()`: Fetches trials + detailed NCT summaries
- `_run_market_agent()`: Retrieves web + RAG sources (top_k_rag=15, top_k_web=80)
- `_fuse_results()`: Merges agent outputs into unified response with confidence scoring
- `_synthesize_overview_summary()`: LLM-powered synthesis from multiple agents

**Critical Configurations**:
- Clinical: Fetches detailed summaries for ALL trials (can be slow for 100+ trials)
- Market: top_k_rag=15 internal docs, top_k_web=80 raw → ~25-30 after dedup
- Both agents: Run in sequence (not parallel) with execution status tracking

#### 2. Clinical Agent (`agents/clinical_agent.py`)
**API**: ClinicalTrials.gov API v2
**LLM**: Groq (keyword extraction) + Gemini/Groq (summary synthesis)

**Workflow**:
1. **Keyword Extraction**: Groq sanitizes query → clean API search terms
2. **Trial Search**: ClinicalTrials.gov API (max 1000 trials per query)
3. **Summary Generation**: Gemini generates comprehensive 8-section literature review
4. **Trial Details**: Fetches individual NCT summaries for frontend references

**Output Contract**:
```python
{
  "summary": str,                    # Basic summary
  "comprehensive_summary": str,      # Full 8-section review
  "trials": List[Dict],              # NCT IDs + titles
  "references": List[Reference],     # Formatted for frontend
  "total_trials": int
}
```

**Known Issues**:
- Keyword sanitization critical (API rejects formatted text)
- Gemini preferred for long-form summaries (16K token limit)
- Groq fallback if Gemini fails
- Structured fallback if both LLMs fail (generates from trial data)

#### 3. Market Agent Hybrid (`agents/market_agent_hybrid.py`)
**Retrieval Strategy**: Web Search + RAG (Vector Store)

**Components**:
- **Web Search**: Multi-query approach with domain filtering (Tier 1/2/3 sources)
- **RAG Engine**: ChromaDB vector store with pharmaceutical corpus
- **Confidence Scorer**: Calculates confidence based on source quality + forecast coherence
- **Keyword Extractor**: LLM + deterministic fallback for search queries
- **Section Synthesizer**: Generates 7 structured sections independently
- **Forecast Reconciler**: Aligns conflicting market projections

**Multi-Query Web Search**:
- Uses 3-6 keyword queries per request (not single query)
- Retrieves ~8 results/keyword → ~50-80 raw results
- Deduplicates by URL
- Filters by domain tier (Tier 1: IQVIA, Evaluate Pharma, etc.)
- Returns top_k weighted by relevance + recency

**Output Contract**:
```python
{
  "agentId": "market",
  "query": str,
  "sections": {                      # 7 sections
    "summary": str,
    "market_overview": str,
    "key_metrics": str,
    "drivers_and_trends": str,
    "competitive_landscape": str,
    "risks_and_opportunities": str,
    "future_outlook": str
  },
  "confidence": {
    "score": float,                  # 0.0-1.0
    "breakdown": Dict,               # Component scores
    "explanation": str,
    "level": str                     # high/medium/low
  },
  "web_results": List[Dict],         # Raw web sources
  "rag_results": List[Dict],         # RAG documents
  "sources": {
    "web": List[str],                # URLs
    "internal": List[str]            # Doc IDs
  }
}
```

**Confidence Calculation**:
- Source coverage (30%): # sources vs expected
- Source quality (25%): Domain tier weighting
- Citation density (20%): LLM cites sources
- Data freshness (15%): Recent sources preferred
- Forecast coherence (10%): Forecast reconciliation boost

#### 4. API Routes (`api/routes.py`)
**Endpoint**: `POST /api/query`

**Request**:
```python
{"query": "GLP-1 market opportunity"}
```

**Response**: Combined output from Master Agent (includes both agents' data)

**Key Response Fields**:
- `summary`: Overview synthesis from all agents
- `insights`: Array of agent findings with confidence
- `references`: Unified references with `agentId` filter
- `market_intelligence`: Full market data (7 sections + confidence)
- `confidence_score`: Aggregate confidence (0-100)
- `agent_execution_status`: Real-time execution tracking
- `total_trials`: Clinical trial count

### Frontend Architecture (`/frontend/src/pages/ResearchPage.tsx`)

#### Component Structure
**Main Views**:
1. **Query Input**: Search bar + sample queries
2. **Agent Sidebar**: Real-time agent status (idle/running/complete)
3. **Results Tabs**: Overall / Clinical / Market / Other
4. **Reference Cards**: Filterable by agentId with NCT links

**State Management**:
- `results`: Full API response
- `activeAgents`: Currently executing agents (from backend)
- `activeTab`: Selected view (overall/clinical/market)
- `agentLogs`: Real-time execution logs
- `selectedAgent`: Modal view for agent details

**Tab Filtering Logic**:
```typescript
// CRITICAL: Defensive filtering with strict agentId enforcement
switch (activeTab) {
  case 'clinical':
    return results.references.filter(ref => ref.agentId === 'clinical');
  case 'market':
    return results.references.filter(ref => ref.agentId === 'market');
  case 'overall':
    return results.references;  // All references
}
```

**Real-time Updates**:
- Polls `agent_execution_status` from API response
- Updates agent status: idle → running → complete
- Displays execution logs and result counts

### Integration Flow

```
1. User Query
   ↓
2. POST /api/query → Master Agent
   ↓
3. Query Classification
   ↓ ↓ ↓
4a. Clinical Agent        4b. Market Agent
   - Groq keywords           - Multi-query web search
   - ClinicalTrials.gov      - RAG retrieval
   - Gemini synthesis        - Confidence scoring
   - Trial summaries         - Section synthesis
   ↓                        ↓
5. Result Fusion (Master Agent)
   - Merge references (with agentId)
   - Calculate aggregate confidence
   - Synthesize overview (LLM)
   ↓
6. Unified Response
   - 7 market sections
   - N clinical trial references
   - Aggregate confidence
   - Execution status
   ↓
7. Frontend Rendering
   - Tab-based view
   - Filterable references
   - NCT hyperlinks
   - Export functionality
```

### Critical Dependencies

**Backend**:
- `GROQ_API_KEY`: Keyword extraction, fallback synthesis
- `GOOGLE_API_KEY` (Gemini): Preferred for long-form summaries
- `SERPAPI_KEY`: Web search (required for market agent)
- ChromaDB: Vector store (auto-initializes corpus)

**Frontend**:
- `REACT_APP_API_URL`: Backend endpoint (default: http://localhost:8000)
- Framer Motion: Animations
- Lucide React: Icons

### Known Issues & Workarounds

**Backend**:
1. **Empty Trial Results**: Check keyword sanitization logs (removes bullets, numbers)
2. **Web Search Fails**: Verify SERPAPI_KEY is set; agent falls back to RAG only
3. **Low Confidence**: Often due to insufficient web sources or RAG corpus size
4. **Slow Queries**: Clinical agent fetches ALL trial summaries (100+ trials = 60s+)

**Frontend**:
1. **References Not Filtering**: Check `agentId` is set in backend response
2. **Tab Not Glowing**: Verify `activeAgents` includes agent ID during processing
3. **NCT Links Broken**: Ensure NCT ID format is `NCT\d{8}` in regex
4. **Export Incomplete**: PDF export is plain text (not actual PDF)

**Integration**:
1. **CORS Errors**: Backend must allow frontend origin (FastAPI CORS middleware)
2. **Empty Market Section**: Check SERPAPI_KEY and Gemini API quota
3. **Confidence Always Low**: Verify web search returns results (check logs)

### Diagnostic Commands

**Backend Health Check**:
```bash
cd backend
python -c "from agents.master_agent import MasterAgent; a=MasterAgent(); print('✅ OK')"
python -c "from agents.clinical_agent import ClinicalAgent; a=ClinicalAgent(); print('✅ OK')"
python -c "from agents.market_agent_hybrid import MarketAgentHybrid; a=MarketAgentHybrid(); print('✅ OK')"
```

**API Key Verification**:
```bash
echo "Groq: ${GROQ_API_KEY:0:10}..."
echo "Gemini: ${GOOGLE_API_KEY:0:10}..."
echo "SerpAPI: ${SERPAPI_KEY:0:10}..."
```

**Frontend Build Check**:
```bash
cd frontend
npm list react framer-motion lucide-react
npm run build  # Should complete without errors
```

**Test Query**:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "GLP-1 market size 2024"}'
```

## Notes
- Update this file when workflows or policies change.
- Keep secrets and keys out of prompts and logs.
- All agent responses use structured JSON contracts for type safety.
- Frontend filters references by `agentId` for clean separation.
- Master Agent synthesizes overview AFTER all agents complete (not during).
- Market Agent uses multi-query web search for better coverage (not single query).
