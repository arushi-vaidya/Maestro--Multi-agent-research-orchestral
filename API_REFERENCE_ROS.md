# API Reference: ROS Scoring Methods

## Endpoints

### POST /api/query

Main query processing endpoint that now supports both ROS methods.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body - Deterministic (Original):**
```json
{
  "query": "GLP-1 receptor agonists for type 2 diabetes"
}
```

**Body - Gemini Honest (New):**
```json
{
  "query": "GLP-1 receptor agonists for type 2 diabetes",
  "ros_method": "gemini_honest"
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Pharmaceutical research query |
| `ros_method` | string | No | "deterministic" | ROS calculation method: "deterministic" or "gemini_honest" |

#### Response

Both methods return same response structure with different score origins.

**Deterministic Response:**
```json
{
  "query_id": "uuid-here",
  "query": "GLP-1 for type 2 diabetes",
  "summary": "Research summary...",
  "insights": [...],
  "recommendation": "Recommendation text...",
  "references": [...],
  "confidence_score": 5.2,
  "active_agents": ["clinical", "market"],
  "agent_execution_status": [...],
  "market_intelligence": {...}
}
```

**Gemini Honest Response:**
```json
{
  "query_id": "uuid-here", 
  "query": "GLP-1 for type 2 diabetes",
  "summary": "Research summary...",
  "insights": [...],
  "recommendation": "Recommendation text...",
  "references": [...],
  "confidence_score": 4.8,
  "active_agents": ["clinical", "market"],
  "agent_execution_status": [...],
  "market_intelligence": {...}
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `query_id` | string | Unique ID for this query execution |
| `query` | string | Echo of input query |
| `summary` | string | Synthesis of findings |
| `insights` | array | Agent findings with confidence |
| `recommendation` | string | Research recommendation |
| `references` | array | Evidence sources with metadata |
| `confidence_score` | float | 0-100 aggregate confidence |
| `active_agents` | array | Agents that ran: ["clinical", "market"] |
| `agent_execution_status` | array | Detailed execution tracking |
| `market_intelligence` | object | Full market data (7 sections + confidence) |

#### ROS Score Info

The ROS score is embedded in the response from the master agent processing.

**To access ROS score specifically:**
- It's included in agent insights
- Also cached internally for retrieval via API façade

---

## Examples

### Example 1: Quick Deterministic Score

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "CRISPR for sickle cell disease"
  }'
```

Response includes fast deterministic ROS calculation.

### Example 2: Gemini Honest Assessment

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "CRISPR for sickle cell disease",
    "ros_method": "gemini_honest"
  }'
```

Response includes Gemini's brutally honest assessment.

### Example 3: Using jq to Extract ROS

```bash
# Deterministic
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "GLP-1 for diabetes"}' | jq '.confidence_score'

# Gemini
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "GLP-1 for diabetes", "ros_method": "gemini_honest"}' \
  | jq '.confidence_score'
```

### Example 4: Python Client

```python
import requests

# Deterministic
response = requests.post(
    "http://localhost:8000/api/query",
    json={"query": "CRISPR for sickle cell"}
)
print(response.json()['confidence_score'])

# Gemini
response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "CRISPR for sickle cell",
        "ros_method": "gemini_honest"
    }
)
print(response.json()['confidence_score'])
```

### Example 5: Compare Methods

```bash
#!/bin/bash

QUERY="GLP-1 for type 2 diabetes"

echo "Deterministic ROS:"
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\"}" | jq '.confidence_score'

echo "Gemini ROS:"
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\", \"ros_method\": \"gemini_honest\"}" \
  | jq '.confidence_score'
```

---

## Error Handling

### Success (Both Methods Work)
```json
{
  "confidence_score": 5.2,
  "summary": "...",
  ...
}
```

### Fallback (Gemini Fails → Deterministic)
```json
{
  "confidence_score": 5.2,  // From deterministic fallback
  "summary": "...",
  ...
  // Note: Gemini assessment not included, but deterministic result still valid
}
```

### Failure (No Method Works)
```json
{
  "detail": "Error processing query: ..."
}
```

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success - ROS calculated (either method) |
| 400 | Bad request - missing required parameter |
| 422 | Validation error - invalid parameter |
| 500 | Server error - contact administrator |

---

## Performance Metrics

### Deterministic
- **Speed**: <50ms
- **Cost**: $0
- **Consistency**: 100% reproducible
- **API Calls**: 0

### Gemini Honest
- **Speed**: 2-5 seconds
- **Cost**: ~$0.001 per call
- **Consistency**: ~95% (±0.5 variation)
- **API Calls**: 1 (to Gemini)

### Total (Including Query Processing)
- **Deterministic**: 1-2 seconds (master agent + ROS)
- **Gemini**: 3-7 seconds (master agent + ROS + Gemini)

---

## Rate Limiting

- **No internal rate limit** on `/api/query`
- **Gemini API limit**: 15 calls/minute (free tier)
- **Recommendation**: Cache results or use deterministic for high volume

---

## Configuration

### Environment Variables
Location: `backend/.env`

```bash
GOOGLE_API_KEY=AIzaSyCbTUN...  # Required for Gemini method
GROQ_API_KEY=gsk_...           # Required for clinical agent
SERPAPI_API_KEY=...            # Required for market agent
```

### API Settings (in `backend/ros/scorer.py`)
```python
# Gemini model configuration
model = genai.GenerativeModel('gemini-2.5-flash')

# Generation parameters
generation_config=genai.GenerationConfig(
    temperature=0.3,          # Adjust 0.0-1.0
    max_output_tokens=1500    # Adjust as needed
)
```

---

## Troubleshooting

### "InvalidApiKey" Error
```
Error: Unauthorized - Invalid API key
```
**Solution:** Verify `GOOGLE_API_KEY` in `backend/.env`

### "ros_method not recognized"
```
{
  "detail": "ros_method should be 'deterministic' or 'gemini_honest'"
}
```
**Solution:** Use valid method: `"deterministic"` or `"gemini_honest"`

### Gemini Timeout
```
Error: Timeout - Gemini API call exceeded 30 seconds
```
**Solution:** Automatically falls back to deterministic. Check network.

### Missing GOOGLE_API_KEY
```
[ROS] GOOGLE_API_KEY not set - Gemini ROS scoring will not be available
```
**Solution:** Add `GOOGLE_API_KEY` to `backend/.env` and restart backend

---

## Integration Examples

### Frontend (React)

```typescript
// Deterministic
const response1 = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: "My research query" })
});

// Gemini Honest
const response2 = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "My research query",
    ros_method: "gemini_honest"
  })
});
```

### Backend (Python)

```python
from api.routes import process_query
from fastapi import Request

# Simulate request
class MockRequest:
    query = "CRISPR for sickle cell"
    ros_method = "gemini_honest"

result = process_query(MockRequest())
```

---

## Monitoring

### Enable Debug Logging
Edit `backend/main.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # Was INFO
```

### Monitor Gemini Calls
Search logs for:
```
[ROS-GEMINI] Calling Gemini API
[ROS-GEMINI] Gemini score:
```

### Track API Usage
```bash
# Count Gemini calls
grep -c "Calling Gemini API" backend/logs/*.log

# Check for fallbacks
grep -c "fallback_deterministic" backend/logs/*.log
```

---

## Future Enhancements

- [ ] Caching layer for duplicate queries
- [ ] Batch evaluation for cost optimization
- [ ] Custom prompts per therapeutic area
- [ ] Comparative scoring (vs competitors)
- [ ] Historical scoring trends
- [ ] Integration with external scoring models

---

**Last Updated:** May 7, 2026  
**API Version:** 1.0  
**ROS Methods:** Deterministic + Gemini Honest
