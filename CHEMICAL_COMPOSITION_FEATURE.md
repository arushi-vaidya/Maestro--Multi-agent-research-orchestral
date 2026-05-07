# Chemical Composition Analysis Feature

## Overview

The Chemical Composition Analysis feature provides detailed molecular and structural analysis of pharmaceutical compounds using the Gemini API. This feature is integrated into the Evidence Timeline page and displays comprehensive information about drug structures, similarities to approved medications, and therapeutic potential.

## Architecture

### Backend Components

#### 1. Chemical Composition Service (`backend/services/chemical_composition_service.py`)

The service handles all chemical analysis using Gemini API:

**Key Features:**
- Chemical formula extraction (e.g., C21H28O5)
- Molecular weight calculation
- IUPAC nomenclature
- Structure-activity relationships (SAR)
- Drug similarity assessment
- Pharmacophore identification
- Safety considerations
- Optimization recommendations

**Main Methods:**

```python
analyze_chemical_composition(compound_name: str, context: Optional[str]) -> Dict[str, Any]
```
Comprehensive analysis of chemical composition with all details.

**Response Structure:**
```python
{
    'compound_name': 'Semaglutide',
    'chemical_formula': 'C187H291N45O59',
    'molecular_weight': 4113.6,
    'iupac_name': '...',
    'chemical_structure': '...',
    'structure_details': '...',
    'pharmacophore_elements': '...',
    'drug_similarity_analysis': '...',
    'similarity_score': 0.85,
    'similar_drugs': ['Liraglutide', 'Dulaglutide'],
    'mechanism_of_action': '...',
    'therapeutic_potential': '...',
    'structure_activity_relationship': '...',
    'key_interactions': '...',
    'safety_considerations': '...',
    'optimization_potential': '...',
    'evidence_confidence': 'HIGH'
}
```

#### 2. API Endpoint

**POST /api/chemical-composition**

Request:
```json
{
    "compound_name": "Semaglutide",
    "context": "GLP-1 receptor agonist for diabetes and weight loss"
}
```

Response: `ChemicalCompositionResponse` model with all analyzed data.

### Frontend Components

#### 1. ChemicalComposition Component (`frontend/src/components/calm/ChemicalComposition.tsx`)

React component for displaying chemical analysis with:
- Expandable sections for each analysis category
- Quick facts panel (formula, MW, similarity score)
- Color-coded confidence levels (HIGH/MEDIUM/LOW)
- Responsive grid layout
- Clean, minimal design

**Props:**
```typescript
interface ChemicalCompositionProps {
  data: ChemicalCompositionResponse;
  isLoading?: boolean;
  isExpanded?: boolean;
}
```

#### 2. API Integration (`frontend/src/services/api.ts`)

New method:
```typescript
analyzeChemicalComposition(request: ChemicalCompositionRequest): Promise<ChemicalCompositionResponse>
```

#### 3. Timeline Integration (`frontend/src/pages/v2/Timeline.tsx`)

The Timeline page automatically:
1. Extracts drug name from the search query
2. Fetches chemical composition data
3. Displays it above the evidence timeline
4. Shows loading state while analyzing

## Usage

### For Users

1. Navigate to the **Evidence Timeline** page
2. Enter a pharmaceutical query (e.g., "Analyze GLP-1 for diabetes")
3. The chemical composition section automatically loads
4. Click the header to expand/collapse the analysis
5. Click individual section headers to see detailed information

### For Developers

#### Using the Chemical Service

```python
from services.chemical_composition_service import ChemicalCompositionService

service = ChemicalCompositionService()
result = service.analyze_chemical_composition(
    compound_name="Aspirin",
    context="NSAIDs for pain relief"
)

print(result['chemical_formula'])  # C9H8O4
print(result['similarity_score'])  # 0.92
```

#### Making API Requests

```javascript
// JavaScript/React
import { api } from './services/api';

const result = await api.analyzeChemicalComposition({
    compound_name: "Aspirin",
    context: "NSAID for pain relief"
});

console.log(result.chemical_formula);    // C9H8O4
console.log(result.similar_drugs);        // Array of similar drugs
```

## Analysis Sections

### 1. Chemical Identification
- Chemical formula (e.g., C9H8O4)
- Molecular weight in g/mol
- IUPAC systematic name
- Common synonyms and brand names

### 2. Chemical Structure
- Core structure description
- Functional groups
- Stereochemistry
- Ring systems

### 3. Detailed Structure Analysis
- Atomic connectivity and bonds
- Electron distribution patterns
- Polar and hydrophobic regions
- Steric considerations

### 4. Pharmacophore Elements
- Key functional groups for activity
- Biological target interactions
- Contribution to therapeutic effect

### 5. Drug Similarity Analysis
- Comparison to 3-5 similar approved drugs
- Structural similarities and differences
- Similarity score (0-1)
- Drug class classification

### 6. Mechanism of Action
- Target protein/receptor
- Binding mechanism
- Downstream effects
- Therapeutic pathway

### 7. Therapeutic Potential
- Clinical indications
- Advantages over existing treatments
- Structural limitations
- Overall potential assessment

### 8. Structure-Activity Relationships (SAR)
- Essential molecular parts
- Modifications for enhancement
- Modifications causing loss of activity
- Structure-toxicity considerations

### 9. Molecular Interactions
- Hydrogen bonding
- Van der Waals forces
- Electrostatic interactions
- Hydrophobic interactions

### 10. Safety Considerations
- Structural alerts (toxicophores)
- Off-target binding potential
- Metabolic stability
- Genotoxicity assessment

### 11. Optimization Potential
- Areas for efficacy improvement
- Selectivity enhancement strategies
- Pharmacokinetic optimization
- Synthetic accessibility

## Configuration

### Environment Variables

Required:
- `GOOGLE_API_KEY`: Gemini API key (same as existing requirement)

### API Key Setup

1. Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Add to `backend/.env`:
   ```
   GOOGLE_API_KEY=your_key_here
   ```

## Performance Considerations

### Latency
- Initial analysis: 2-5 seconds
- Subsequent queries: ~2 seconds (depends on Gemini API)

### Optimization Tips
1. Chemical composition loads in parallel with timeline data
2. Component gracefully degrades if API fails
3. Error messages don't block timeline display
4. Failed requests don't prevent user navigation

### Rate Limits
- Gemini API has generous free tier
- Each analysis uses ~2 API requests
- Monitor usage in Google Cloud Console

## Error Handling

### Backend Errors
```python
# API returns error field if analysis fails
{
    "compound_name": "Unknown123",
    "error": "Failed to analyze chemical composition",
    "evidence_confidence": "LOW",
    "analysis_status": "failed"
}
```

### Frontend Handling
- Shows error card with details
- Allows retry via manual re-query
- Timeline continues working independently

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Empty response | Query too generic | Use specific drug name |
| Timeout | API slow | Retry or check Google Cloud status |
| Missing fields | Gemini model limitations | Use confidence level to assess reliability |

## Testing

### Quick Test
```bash
curl -X POST http://localhost:8000/api/chemical-composition \
  -H "Content-Type: application/json" \
  -d '{
    "compound_name": "Aspirin",
    "context": "Nonsteroidal anti-inflammatory drug"
  }'
```

### Python Test
```python
from backend.services.chemical_composition_service import ChemicalCompositionService

service = ChemicalCompositionService()
result = service.analyze_chemical_composition(
    compound_name="Metformin",
    context="Diabetes medication"
)

# Check key fields
assert 'chemical_formula' in result
assert 'similarity_score' in result
assert result['evidence_confidence'] in ['HIGH', 'MEDIUM', 'LOW']
print("✅ Chemical composition analysis working!")
```

### React Test
```typescript
import { ChemicalComposition } from './components/calm/ChemicalComposition';

// Mock data for testing
const mockData = {
  compound_name: 'Test Drug',
  chemical_formula: 'C9H8O4',
  molecular_weight: 180.16,
  mechanism_of_action: 'Test mechanism',
  evidence_confidence: 'MEDIUM' as const,
};

export default () => (
  <ChemicalComposition data={mockData} />
);
```

## Future Enhancements

### Planned Features
1. **3D Structure Visualization**: Render 3D molecular structures
2. **Patent Analysis**: Link to related patents
3. **Clinical Data Integration**: Connect to clinical trial results
4. **Synthesis Routes**: Suggest synthesis pathways
5. **Export Options**: Download analysis as PDF/Excel
6. **Batch Analysis**: Analyze multiple compounds
7. **Historical Tracking**: Compare analyses over time

### Integration Opportunities
1. Combine with market intelligence for drug potential
2. Link to clinical evidence for validation
3. Create structure-activity recommendation engine
4. Build chemical space explorer

## Troubleshooting

### Backend Issues

**"GOOGLE_API_KEY not found"**
```bash
# Check env file
cat backend/.env | grep GOOGLE_API_KEY

# If missing:
export GOOGLE_API_KEY=your_key
python backend/main.py
```

**Import error: "No module named 'google.generativeai'"**
```bash
pip install google-generativeai
```

### Frontend Issues

**"analyzeChemicalComposition is not a function"**
- Ensure API method is exported from `api.ts`
- Check types are imported correctly

**Component not rendering**
- Verify ChemicalCompositionResponse type matches backend response
- Check browser console for TypeScript errors

### API Issues

**Timeout errors**
- Gemini API may be overloaded
- Retry with exponential backoff
- Check Google Cloud Console for quota issues

**Empty responses**
- Drug name might be unrecognized
- Try with full compound name or context
- Check Gemini API status

## Support

For issues or questions:
1. Check error messages in browser console
2. Review backend logs: `tail -f backend/logs/*.log`
3. Verify API keys are set correctly
4. Test endpoint directly with curl

## Related Documentation

- [Gemini API Documentation](https://ai.google.dev/)
- [Evidence Timeline Guide](./EVIDENCE_TIMELINE.md)
- [Backend Architecture](./backend/README_STRUCTURE.md)
- [Frontend Components](./frontend/src/components/README.md)
