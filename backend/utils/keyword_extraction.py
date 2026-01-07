"""
Robust Keyword Extraction for Market Intelligence
Combines LLM extraction with deterministic fallback for reliability
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """
    Robust keyword extraction with deterministic fallback
    Ensures high-quality search keywords even when LLM fails
    """

    def __init__(self):
        # Domain-specific entity patterns
        self.drug_patterns = [
            'glp-1', 'glp1', 'ozempic', 'wegovy', 'mounjaro', 'semaglutide',
            'tirzepatide', 'dulaglutide', 'liraglutide', 'insulin',
            'keytruda', 'opdivo', 'tecentriq', 'leqembi', 'donanemab'
        ]

        self.company_patterns = [
            'novo nordisk', 'eli lilly', 'pfizer', 'roche', 'merck',
            'bristol myers squibb', 'bms', 'astrazeneca', 'sanofi',
            'biogen', 'eisai', 'abbvie', 'gilead', 'amgen'
        ]

        self.therapy_areas = [
            'diabetes', 'obesity', 'oncology', 'cancer', 'alzheimer',
            'immunotherapy', 'cardiovascular', 'neurology', 'gene therapy'
        ]

    def extract_keywords_robust(
        self,
        query: str,
        llm_extracted: List[str] = None
    ) -> List[str]:
        """
        Extract high-quality search keywords with LLM + fallback

        Args:
            query: User query
            llm_extracted: Keywords from LLM (optional)

        Returns:
            List of validated, high-quality keywords
        """
        # Validate LLM keywords if provided
        if llm_extracted and self._is_valid_keywords(llm_extracted):
            logger.info(f"Using LLM keywords: {llm_extracted}")
            return llm_extracted[:3]

        # Fall back to deterministic extraction
        logger.info("LLM keywords invalid or unavailable, using deterministic extraction")
        return self._generate_fallback_keywords(query)

    def _is_valid_keywords(self, keywords: List[str]) -> bool:
        """
        Validate keyword quality

        Rejects:
        - Keywords too long (>8 words)
        - Keywords containing question words
        - Empty keywords
        """
        if not keywords:
            return False

        question_words = [
            'what', 'is', 'are', 'how', 'when', 'where', 'why',
            'which', 'who', 'whom', 'whose', 'does', 'do', 'did',
            'can', 'could', 'will', 'would', 'should', 'tell', 'me',
            'about', 'the'
        ]

        for kw in keywords:
            kw_lower = kw.lower().strip()

            # Empty keyword
            if not kw_lower:
                return False

            # Too long (likely a full sentence)
            if len(kw_lower.split()) > 8:
                logger.debug(f"Keyword too long: {kw}")
                return False

            # Contains question words (not focused enough)
            if any(qw in kw_lower.split() for qw in question_words):
                logger.debug(f"Keyword contains question word: {kw}")
                return False

        return True

    def _generate_fallback_keywords(self, query: str) -> List[str]:
        """
        Generate focused keywords using pattern matching

        Strategy:
        1. Extract entities (drugs, companies, therapy areas)
        2. Identify query intent (market size, forecast, revenue)
        3. Combine into focused search terms
        """
        query_lower = query.lower()
        keywords = []

        # Extract entities
        drugs_found = [d for d in self.drug_patterns if d in query_lower]
        companies_found = [c for c in self.company_patterns if c in query_lower]
        therapy_areas_found = [t for t in self.therapy_areas if t in query_lower]

        # Identify intent
        has_market_size = any(term in query_lower for term in ['market', 'size'])
        has_forecast = any(term in query_lower for term in ['forecast', 'projection', 'outlook', 'future'])
        has_revenue = any(term in query_lower for term in ['revenue', 'sales'])
        has_growth = any(term in query_lower for term in ['growth', 'cagr'])

        # Generate focused keywords from entities + intent
        for drug in drugs_found[:2]:  # Limit to 2 drugs
            if has_market_size:
                keywords.append(f"{drug} market size 2024")
            if has_forecast:
                keywords.append(f"{drug} market forecast 2030")
            if has_revenue or has_growth:
                keywords.append(f"{drug} sales revenue 2024")

        for company in companies_found[:2]:
            if has_revenue:
                keywords.append(f"{company} revenue 2024")
            if has_market_size or has_forecast:
                keywords.append(f"{company} market share")

        for therapy in therapy_areas_found[:2]:
            if has_market_size:
                keywords.append(f"{therapy} pharmaceutical market size")
            if has_forecast:
                keywords.append(f"{therapy} market forecast")

        # If no entities found, extract from query directly
        if not keywords:
            keywords = self._extract_from_query_directly(query_lower)

        # Deduplicate and limit
        keywords = list(dict.fromkeys(keywords))  # Preserve order, remove dupes

        return keywords[:3]  # Max 3 keywords

    def _extract_from_query_directly(self, query_lower: str) -> List[str]:
        """
        Extract keywords when no entities found
        Uses simple heuristics to create focused searches
        """
        keywords = []

        # Remove common question words
        query_clean = re.sub(
            r'\b(what|is|are|how|when|where|why|which|the|a|an|for|about|tell|me)\b',
            '',
            query_lower
        )
        query_clean = ' '.join(query_clean.split())  # Remove extra spaces

        # Truncate if too long
        if len(query_clean) > 50:
            query_clean = query_clean[:50]

        # Add context for pharma market intelligence
        keywords.append(f"{query_clean} pharmaceutical market 2024")
        keywords.append(f"{query_clean} market analysis")

        # Generic fallback
        if not query_clean:
            keywords = [
                "pharmaceutical market intelligence 2024",
                "biotech market analysis"
            ]

        return keywords


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    extractor = KeywordExtractor()

    test_cases = [
        # Good LLM output
        ("What is GLP-1 market?", ["GLP-1 market size", "GLP-1 forecast"]),

        # Bad LLM output (too long)
        ("What is GLP-1 market?", ["What is the GLP-1 agonist market size and forecast for 2024?"]),

        # Bad LLM output (question words)
        ("GLP-1 Novo revenue", ["What is the GLP-1 revenue"]),

        # No LLM output
        ("What is the Ozempic market size in 2024?", None),

        # Company query
        ("Tell me about Eli Lilly diabetes revenue", None),

        # Generic query
        ("Pharmaceutical market analysis", None),
    ]

    for query, llm_output in test_cases:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print(f"LLM Output: {llm_output}")

        keywords = extractor.extract_keywords_robust(query, llm_output)

        print(f"Final Keywords: {keywords}")
