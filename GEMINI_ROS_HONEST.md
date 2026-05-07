# Gemini-Based ROS Scoring - Brutally Honest Evaluation

## Overview

The system now supports **two methods for calculating Research Opportunity Scores (ROS)**:

1. **Deterministic ROS** (original): Component-based formula with transparent weights
2. **Gemini ROS** (new): Direct Gemini API evaluation with "brutally honest" feedback

## The Gemini Approach

Instead of using predefined weights and component calculations, the new method passes your research query directly to Claude/Gemini and asks for an honest assessment of:

- **Actual novelty level** (calls out market saturation)
- **Major evidence limitations** (no sugar-coating)
- **Realistic market risks** (freedom-to-operate, patent density, etc.)
- **Research opportunity score** (0-10, conservative)

### Key Features

✅ **Brutal Honesty**: Doesn't inflate scores for saturated markets  
✅ **Evidence-Aware**: Considers clinical trials, literature, patents, market data  
✅ **Risk Assessment**: Flags patent risks, conflicting evidence, limited data  
✅ **Realistic Scoring**: Conservative estimates (rarely gives 9-10)  
✅ **Transparent Reasoning**: Explains the score in detail  

## Usage

### Python Code

```python
from ros.scorer import calculate_ros_with_gemini

# Your data
query = "GLP-1 receptor agonists for type 2 diabetes"
references = [...]  # Clinical trials, literature, patents, market data
insights = [...]    # Research insights from agents

# Call Gemini for honest ROS evaluation
result = calculate_ros_with_gemini(query, references, insights)

print(f"ROS Score: {result['ros_score']:.1f}/10")
print(f"Assessment: {result['gemini_assessment']}")
```

### API Endpoint (Coming Soon)

```bash
POST /api/query?method=gemini_honest

{
  "query": "Drug X for Disease Y"
}

Response:
{
  "ros_score": 6.5,
  "calculation_method": "gemini_honest",
  "gemini_assessment": "Strong opportunity but patent landscape is crowded...",
  "metadata": {...}
}
```

## Scoring Guide (Gemini)

| Score | Interpretation |
|-------|-----------------|
| 9-10 | **Exceptional** - Rare opportunity. Novel indication, strong evidence, clear market gap |
| 7-8 | **Good** - Strong evidence, moderate novelty, real potential |
| 5-6 | **Moderate** - Mixed signals. Some novelty OR good evidence but not both |
| 3-4 | **Weak** - Limited evidence, high saturation, or unproven mechanism |
| 0-2 | **Poor** - Insufficient evidence, saturated market, major red flags |

## What Gemini Evaluates

### Evidence Quality
- Number and type of clinical trials
- Relevance and quality of literature
- Patent landscape and freedom-to-operate
- Market data and demand signals

### Novelty Assessment
- How many existing trials for this indication?
- What trial phases are active? (Phase 1 = novel, Phase 4 = mature)
- Is this a new indication or well-established?

### Risk Factors
- Patent saturation (many patents = limited opportunity)
- Conflicting evidence (positive vs negative results)
- Unproven mechanisms or safety concerns
- Market size and growth potential

### Market Realism
- Is this a crowded space?
- What's the competitive landscape?
- Are there real regulatory pathways?

## Configuration

### Environment Variables
```bash
# Required for Gemini scoring
export GOOGLE_API_KEY="your-gemini-api-key"
```

### Fallback Behavior
If Gemini API fails, the system automatically falls back to deterministic scoring:

```python
result = calculate_ros_with_gemini(...)
# If Gemini call fails:
# - Falls back to calculate_ros()
# - Returns {"calculation_method": "fallback_deterministic", ...}
```

## Example Output

```
Query: CRISPR for sickle cell disease

ROS Score: 7.8/10

Gemini's Assessment:
This is a genuine opportunity with compelling clinical evidence. Phase 3 data from 
Vertex's trials show sustained improvements in patient outcomes. However, several 
factors temper the score:

1. NOVELTY: MODERATE - CRISPR for blood disorders is no longer novel. Multiple 
   companies are in late-stage development. This is an established, crowded space.

2. EVIDENCE LIMITATIONS: 
   - Phase 3 data is from single sponsor (Vertex)
   - Long-term safety data limited to <3 years follow-up
   - Real-world effectiveness in diverse populations unclear

3. MARKET RISKS:
   - Patent landscape shows ~15 blocking patents
   - Manufacturing capacity constraints
   - Pricing pressure from competing gene therapies

4. What Would Make It Better:
   - Independent Phase 3 confirmation from different sponsor
   - 5+ year safety data
   - Evidence in additional blood disorders

HONEST SCORE: 7.8/10 - Good opportunity but realistic about crowded space.
```

## Comparison: Deterministic vs Gemini

| Aspect | Deterministic | Gemini |
|--------|--------------|--------|
| **Speed** | Instant (no API calls) | 2-5 seconds (API call) |
| **Transparency** | Full component breakdown | Narrative explanation |
| **Bias Risk** | Weighted averages might miss saturation | LLM-aware of market context |
| **Customization** | Tune config.py weights | Ask Gemini to focus on different factors |
| **Cost** | Free | ~$0.001 per evaluation |
| **Audit Trail** | Component scores | Full reasoning in plain English |

## When to Use Each

**Use Deterministic ROS when:**
- Fast decisions needed (no API latency)
- Exact reproducibility required
- Cost is critical (zero API calls)
- You want explicit weight breakdown

**Use Gemini ROS when:**
- Honest assessment needed (not inflated scores)
- You want risk commentary
- You need narrative explanation
- API costs acceptable
- Team decision-making needed

## Implementation Details

### Score Extraction
Gemini returns narrative text. The system extracts numeric scores via:
1. Pattern matching: "score: 7.5", "ROS: 8", "7.5/10"
2. Context search: Numbers near "research opportunity"
3. Default fallback: 5.0 if extraction fails (logged as warning)

### Prompting Strategy
- **Temperature 0.3** for focused, consistent answers
- **System prompt** establishes brutal honesty expectation
- **User prompt** provides evidence context + asks for honest score
- **Max tokens** 1500 for detailed reasoning

## Troubleshooting

### API Key Not Set
```
❌ GOOGLE_API_KEY not set
Set it before running:
   export GOOGLE_API_KEY='your-api-key'
```
Get a free key: https://aistudio.google.com/app/apikey

### Score Extraction Failed
```
[WARNING] Could not extract score from Gemini response, defaulting to 5.0
```
The system tried to find a numeric score in Gemini's response but failed. 
The narrative assessment is still useful; review it directly.

### Gemini API Timeout
```
Error calling Gemini: Timeout after 30 seconds
Falling back to deterministic scoring
```
API call took too long. System uses deterministic scoring instead.

## Future Enhancements

- [ ] Tune prompting for different therapeutic areas
- [ ] Add ablation study mode (e.g., "score without patents")
- [ ] Integration with clinical trial registry APIs for real-time saturation
- [ ] Comparative scoring (e.g., "vs similar programs")
- [ ] Batch evaluation with cost optimization

## References

- [Gemini API Docs](https://ai.google.dev/docs)
- [Research Opportunity Scoring Methodology](./ROS_IMPLEMENTATION_SUMMARY.md)
- [Deterministic ROS Component Breakdown](./ros_config.py)
