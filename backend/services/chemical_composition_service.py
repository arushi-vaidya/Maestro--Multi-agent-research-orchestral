"""
Chemical Composition Analysis Service

Uses Gemini API to analyze:
- Chemical formula and structure
- Molecular properties
- Similarities to drugs in use
- Mechanism of action and usefulness
- Structure-activity relationships

This service provides detailed chemical intelligence for pharmaceutical compounds.
"""

import logging
import json
import re
import time
from typing import Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)
load_dotenv()

class ChemicalCompositionService:
    """Analyzes chemical composition and structure using Gemini API"""

    def __init__(self):
        """Initialize Gemini API client"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        # Try models in order of preference
        model_names = [
            'gemini-2.5-flash',
            'gemini-1.5-flash',
            'gemini-1.0-pro',
            'gemini-pro',
            'gemini-pro-vision',
        ]
        
        self.model = None
        last_error = None
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"✅ Using Gemini model: {model_name}")
                self.model_name = model_name
                break
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️  Model {model_name} not available")
                continue
        
        if self.model is None:
            # If no model works, raise error with helpful message
            raise ValueError(
                f"No available Gemini model found. Last error: {last_error}. "
                f"Check GOOGLE_API_KEY and model availability at https://ai.google.dev/"
            )
        
    def analyze_chemical_composition(self, compound_name: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive chemical composition analysis using Gemini.
        
        Args:
            compound_name: Name of the chemical compound or drug
            context: Additional context (e.g., indication, mechanism)
            
        Returns:
            Dict containing:
            - chemical_formula: Molecular formula (e.g., C21H28O5)
            - chemical_structure: Detailed structure description
            - molecular_weight: MW in g/mol
            - iupac_name: IUPAC systematic name
            - structure_details: Full structural explanation
            - pharmacophore_elements: Key functional groups
            - drug_similarity_analysis: Comparison to similar approved drugs
            - similarity_score: How similar to existing drugs (0-1)
            - similar_drugs: List of similar approved medications
            - mechanism_of_action: How it works
            - therapeutic_potential: Clinical usefulness assessment
            - structure_activity_relationship: SAR insights
            - key_interactions: Important molecular interactions
            - safety_considerations: Structural alerts
            - optimization_potential: Areas for improvement
            - evidence_confidence: Confidence in the analysis
        """
        try:
            prompt = self._construct_prompt(compound_name, context)
            response = self._generate_with_retry(prompt, compound_name)
            
            if not response or not response.text:
                logger.warning(f"Empty response from Gemini for {compound_name}")
                return self._create_empty_response(compound_name)
            
            parsed = self._parse_gemini_response(response.text, compound_name)
            return parsed
            
        except Exception as e:
            logger.error(f"Error analyzing chemical composition for {compound_name}: {str(e)}")
            return self._create_error_response(compound_name, str(e))

    def _generate_with_retry(self, prompt: str, compound_name: str):
        """
        Generate Gemini content with timeout, retry, and compact-prompt fallback.
        Helps recover from transient 429/503/504 failures.
        """
        attempts = 3
        for attempt in range(1, attempts + 1):
            try:
                return self.model.generate_content(prompt)
            except Exception as e:
                message = str(e)
                retriable = any(code in message for code in ["429", "503", "504", "timed out", "deadline"])
                if not retriable or attempt == attempts:
                    raise

                # Final retry uses a smaller prompt to reduce generation latency.
                if attempt == attempts - 1:
                    logger.warning(
                        f"Attempt {attempt}/{attempts} failed for {compound_name}. "
                        "Switching to compact prompt for final attempt."
                    )
                    prompt = self._construct_compact_prompt(compound_name)
                else:
                    logger.warning(
                        f"Attempt {attempt}/{attempts} failed for {compound_name}: {message}. Retrying..."
                    )

                time.sleep(min(2 * attempt, 4))
    
    def _construct_prompt(self, compound_name: str, context: Optional[str]) -> str:
        """Construct compact prompt for faster, more reliable analysis."""
        context_line = f"Context: {context}\n" if context else ""
        return f"""Analyze chemical composition for compound: {compound_name}
{context_line}
Return ONLY valid JSON with EXACT keys:
compound_name, chemical_formula, molecular_weight, iupac_name,
chemical_structure, structure_details, pharmacophore_elements,
drug_similarity_analysis, similarity_score, similar_drugs,
mechanism_of_action, therapeutic_potential, structure_activity_relationship,
key_interactions, safety_considerations, allergy_medical_cautions,
suggested_alternatives, optimization_potential, smiles,
evidence_confidence.

Rules:
- Use concise scientific language.
- Keep each text field <= 120 words.
- similarity_score must be numeric in [0, 1].
- similar_drugs must be an array of drug names (max 5).
- smiles must be a canonical SMILES string if known, else "Not publicly available".
- evidence_confidence must be one of: HIGH, MEDIUM, LOW.
- If unknown, use "Not publicly available".
"""

    def _construct_compact_prompt(self, compound_name: str) -> str:
        """Smaller fallback prompt for timeout/retry scenarios."""
        return f"""Analyze chemical composition for: {compound_name}

Return ONLY valid JSON with these keys:
compound_name, chemical_formula, molecular_weight, iupac_name,
chemical_structure, pharmacophore_elements, drug_similarity_analysis,
similarity_score, similar_drugs, mechanism_of_action, therapeutic_potential,
structure_activity_relationship, key_interactions, safety_considerations,
allergy_medical_cautions, suggested_alternatives, optimization_potential,
smiles, evidence_confidence.

Rules:
- Keep each text field concise (2-4 sentences).
- evidence_confidence must be HIGH, MEDIUM, or LOW.
- similarity_score must be a number between 0 and 1.
"""
    
    def _parse_gemini_response(self, response_text: str, compound_name: str) -> Dict[str, Any]:
        """Parse Gemini response into structured data"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # If JSON parsing fails, create structured response from text
                    data = self._extract_data_from_text(response_text)
            else:
                data = self._extract_data_from_text(response_text)
            
            # Normalize keys to snake_case
            normalized = self._normalize_keys(data)
            normalized = self._sanitize_for_response_schema(normalized)
            
            # Add metadata
            normalized['compound_name'] = compound_name
            normalized['analysis_type'] = 'full_chemical_composition'
            normalized['evidence_confidence'] = normalized.get('evidence_confidence', 'MEDIUM')
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return self._create_error_response(compound_name, str(e))
    
    def _extract_data_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured data from plain text response"""
        data = {
            'full_response': text,
            'analysis_status': 'text_response_parsed'
        }
        
        # Try to extract key information from text using regex patterns
        patterns = {
            'chemical_formula': r'(?:Chemical Formula|Formula):\s*([C0-9H\-\(\)NOS]+)',
            'molecular_weight': r'(?:Molecular Weight|MW):\s*(\d+(?:\.\d+)?)\s*(?:g/mol)?',
            'iupac_name': r'(?:IUPAC Name|IUPAC):\s*(.+?)(?:\n|$)',
            'mechanism_of_action': r'(?:Mechanism of Action|MOA):\s*(.+?)(?:\n\n|$)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                data[key] = match.group(1).strip()
        
        return data
    
    def _normalize_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert keys to snake_case"""
        normalized = {}
        for key, value in data.items():
            # Convert to snake_case
            snake_key = re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower()
            snake_key = re.sub(r'[^a-z0-9_]', '_', snake_key)
            snake_key = re.sub(r'_+', '_', snake_key).strip('_')
            normalized[snake_key] = value
        return normalized

    def _sanitize_for_response_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce Gemini output into API response-compatible primitive types."""
        string_fields = [
            'chemical_formula',
            'iupac_name',
            'chemical_structure',
            'structure_details',
            'pharmacophore_elements',
            'drug_similarity_analysis',
            'mechanism_of_action',
            'therapeutic_potential',
            'structure_activity_relationship',
            'key_interactions',
            'safety_considerations',
            'allergy_medical_cautions',
            'optimization_potential',
            'smiles',
            'analysis_status',
            'error',
        ]

        def to_text(value: Any) -> str:
            if value is None:
                return ""
            if isinstance(value, str):
                return value.strip()
            if isinstance(value, (int, float, bool)):
                return str(value)
            if isinstance(value, list):
                return "; ".join([to_text(v) for v in value if v is not None]).strip()
            if isinstance(value, dict):
                parts = []
                for k, v in value.items():
                    rendered = to_text(v)
                    if rendered:
                        parts.append(f"{k}: {rendered}")
                return "; ".join(parts).strip()
            return str(value).strip()

        def to_float(value: Any) -> Optional[float]:
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            text = to_text(value)
            match = re.search(r'-?\d+(?:\.\d+)?', text)
            if match:
                try:
                    return float(match.group(0))
                except ValueError:
                    return None
            return None

        for field in string_fields:
            if field in data:
                coerced = to_text(data.get(field))
                if coerced:
                    data[field] = coerced
                else:
                    data.pop(field, None)

        # Numeric fields
        if 'molecular_weight' in data:
            mw = to_float(data.get('molecular_weight'))
            if mw is not None:
                data['molecular_weight'] = mw
            else:
                data.pop('molecular_weight', None)

        if 'similarity_score' in data:
            score = to_float(data.get('similarity_score'))
            if score is not None:
                # If model returns percentage (e.g., 85), normalize to 0-1 scale.
                if score > 1.0:
                    score = score / 100.0
                data['similarity_score'] = max(0.0, min(1.0, score))
            else:
                data.pop('similarity_score', None)

        # List fields
        if 'similar_drugs' in data:
            raw = data.get('similar_drugs')
            if isinstance(raw, list):
                data['similar_drugs'] = [to_text(x) for x in raw if to_text(x)]
            elif isinstance(raw, dict):
                data['similar_drugs'] = [to_text(v) for v in raw.values() if to_text(v)]
            else:
                text = to_text(raw)
                data['similar_drugs'] = [x.strip() for x in re.split(r'[,\n;]+', text) if x.strip()] if text else []
            if not data['similar_drugs']:
                data.pop('similar_drugs', None)

        if 'suggested_alternatives' in data:
            raw = data.get('suggested_alternatives')
            if isinstance(raw, list):
                data['suggested_alternatives'] = [to_text(x) for x in raw if to_text(x)]
            elif isinstance(raw, dict):
                data['suggested_alternatives'] = [to_text(v) for v in raw.values() if to_text(v)]
            else:
                text = to_text(raw)
                data['suggested_alternatives'] = [x.strip() for x in re.split(r'[,\n;]+', text) if x.strip()] if text else []
            if not data['suggested_alternatives']:
                data.pop('suggested_alternatives', None)

        # Confidence field must be enum-like string
        confidence_raw = to_text(data.get('evidence_confidence', 'MEDIUM')).upper()
        if 'HIGH' in confidence_raw:
            data['evidence_confidence'] = 'HIGH'
        elif 'LOW' in confidence_raw:
            data['evidence_confidence'] = 'LOW'
        else:
            data['evidence_confidence'] = 'MEDIUM'

        return data
    
    def _create_empty_response(self, compound_name: str) -> Dict[str, Any]:
        """Create empty response structure"""
        return {
            'compound_name': compound_name,
            'error': 'Empty response from API',
            'chemical_formula': 'Not available',
            'chemical_structure': 'Not available',
            'evidence_confidence': 'LOW',
            'analysis_status': 'failed_empty_response'
        }
    
    def _create_error_response(self, compound_name: str, error: str) -> Dict[str, Any]:
        """Create error response structure"""
        return {
            'compound_name': compound_name,
            'error': error,
            'evidence_confidence': 'LOW',
            'analysis_status': 'failed',
            'chemical_formula': 'Not available',
            'chemical_structure': 'Not available'
        }
    
    def get_similarity_score(self, compound_name: str) -> Dict[str, Any]:
        """
        Quick similarity assessment to known drugs.
        Returns how similar the compound is to existing approved drugs (0-1).
        """
        try:
            prompt = f"""For the compound {compound_name}, provide a quick assessment:
            
1. Is it structurally similar to any approved drugs? (Yes/No)
2. If yes, which drugs? List 2-3 most similar
3. Similarity score on a scale of 0-1 (0=completely novel, 1=very similar to existing drug)
4. Does it belong to a known drug class?

Format as JSON with keys: is_similar, similar_drugs (list), similarity_score (float), drug_class"""
            
            response = self.model.generate_content(prompt)
            
            try:
                json_match = re.search(r'\{[\s\S]*\}', response.text)
                if json_match:
                    data = json.loads(json_match.group())
                    return data
            except:
                pass
            
            return {'raw_response': response.text}
            
        except Exception as e:
            logger.error(f"Error getting similarity score: {str(e)}")
            return {'error': str(e)}


def get_chemical_composition_service() -> ChemicalCompositionService:
    """Factory function to get or create service instance"""
    return ChemicalCompositionService()
