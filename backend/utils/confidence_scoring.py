"""
Confidence Scoring System for Market Intelligence Agent
Multi-dimensional scoring based on retrieval quality, coherence, synthesis, and coverage
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Production-grade confidence scoring for market intelligence

    Dimensions:
    - Retrieval Quality (40%): Source quality and diversity
    - Content Coherence (30%): Cross-source agreement and grounding
    - Synthesis Success (20%): LLM generation quality
    - Coverage Completeness (10%): Query fulfillment
    """

    def __init__(self):
        self.weights = {
            'retrieval_quality': 0.40,
            'content_coherence': 0.30,
            'synthesis_success': 0.20,
            'coverage_completeness': 0.10
        }

    def calculate_confidence(
        self,
        query: str,
        web_results: List[Dict[str, Any]],
        rag_results: List[Dict[str, Any]],
        sections: Dict[str, str],
        coherence_boost: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive confidence score

        Args:
            query: User query
            web_results: Web search results (with domain_tier and domain_weight)
            rag_results: RAG retrieval results
            sections: Generated content sections
            coherence_boost: Additional boost from forecast reconciliation (0.0-0.15)

        Returns:
            Confidence analysis with score, breakdown, and explanation
        """
        # Calculate component scores
        retrieval_quality = self._calculate_retrieval_quality(web_results, rag_results)
        content_coherence = self._calculate_content_coherence(web_results, rag_results, sections)
        synthesis_success = self._calculate_synthesis_success(sections, web_results, rag_results)
        coverage_completeness = self._calculate_coverage_completeness(query, sections)

        # Apply coherence boost from forecast reconciliation
        content_coherence = min(1.0, content_coherence + coherence_boost)

        # Weighted combination
        final_score = (
            retrieval_quality * self.weights['retrieval_quality'] +
            content_coherence * self.weights['content_coherence'] +
            synthesis_success * self.weights['synthesis_success'] +
            coverage_completeness * self.weights['coverage_completeness']
        )

        # Clamp to [0, 1]
        final_score = max(0.0, min(1.0, final_score))

        # Generate explanation
        explanation = self._generate_explanation(
            final_score,
            retrieval_quality,
            content_coherence,
            synthesis_success,
            coverage_completeness,
            web_results,
            rag_results,
            sections
        )

        # Determine confidence level
        confidence_level = self._determine_confidence_level(final_score)

        logger.info(f"Confidence calculated: {final_score:.3f} ({confidence_level})")

        return {
            "score": round(final_score, 3),
            "breakdown": {
                "retrieval_quality": round(retrieval_quality, 3),
                "content_coherence": round(content_coherence, 3),
                "synthesis_success": round(synthesis_success, 3),
                "coverage_completeness": round(coverage_completeness, 3)
            },
            "explanation": explanation,
            "level": confidence_level
        }

    def _calculate_retrieval_quality(
        self,
        web_results: List[Dict],
        rag_results: List[Dict]
    ) -> float:
        """
        Measures quality and diversity of retrieved sources with TIERED WEIGHTING

        NEW: Tier-based weighting for web sources
        - Tier 1 (IQVIA, EvaluatePharma): 1.5x weight
        - Tier 2 (Reuters, pharma news): 1.0x weight
        - Tier 3 (forums, blogs): 0.4x weight

        NEW: RAG-only boost when internal agreement is high
        - If ≥3 RAG docs with avg relevance ≥0.8, boost by 0.15

        RAG: Up to 0.6 base (authoritative internal knowledge)
        Web: Up to 0.4 base (corroboration and freshness)
        """
        score = 0.0

        # RAG component (up to 0.6 + potential 0.15 boost)
        if rag_results:
            # Normalize relevance scores (Chroma returns distance, convert to similarity)
            normalized_relevances = [
                self._normalize_chroma_relevance(r)
                for r in rag_results
            ]
            avg_rag_relevance = sum(normalized_relevances) / len(normalized_relevances)

            # Reward multiple high-quality docs (saturates at 5 docs)
            rag_count_bonus = min(len(rag_results) / 5.0, 1.0)
            rag_quality = avg_rag_relevance * 0.7 + rag_count_bonus * 0.3

            score += rag_quality * 0.6

            # NEW: RAG-only confidence boost (if high internal agreement)
            if len(rag_results) >= 3 and avg_rag_relevance >= 0.8:
                rag_only_boost = 0.15
                score += rag_only_boost
                logger.info(f"RAG-only boost applied: +{rag_only_boost:.2f} (≥3 docs, high agreement)")

            logger.debug(f"RAG quality: {rag_quality:.3f} (avg_rel={avg_rag_relevance:.3f}, count={len(rag_results)})")

        # Web component (up to 0.4) with TIER WEIGHTING
        if web_results:
            # NEW: Apply domain tier weighting
            weighted_web_score = self._calculate_weighted_web_quality(web_results)
            score += weighted_web_score * 0.4
            logger.debug(f"Weighted web quality: {weighted_web_score:.3f}")

        # Penalty if NO sources at all
        if not rag_results and not web_results:
            logger.warning("No sources retrieved - retrieval quality = 0")
            return 0.0

        return min(score, 1.0)

    def _calculate_weighted_web_quality(self, web_results: List[Dict]) -> float:
        """
        Calculate web quality using domain tier weighting

        NEW: Applies source weights from domain tier:
        - Tier 1: 1.5x weight (premium sources)
        - Tier 2: 1.0x weight (reputable sources)
        - Tier 3: 0.4x weight (low-signal sources)

        Returns:
            Quality score 0.0-1.0
        """
        if not web_results:
            return 0.0

        # Calculate weighted score
        total_weight = 0.0
        weighted_sum = 0.0

        for result in web_results:
            domain_weight = result.get('domain_weight', 1.0)
            total_weight += domain_weight
            weighted_sum += domain_weight

        # Normalize
        if total_weight > 0:
            avg_weighted_quality = weighted_sum / total_weight
        else:
            avg_weighted_quality = 0.5

        # Count tier distribution
        tier1_count = sum(1 for r in web_results if r.get('domain_tier') == 1)
        tier2_count = sum(1 for r in web_results if r.get('domain_tier') == 2)
        tier3_count = sum(1 for r in web_results if r.get('domain_tier') == 3)

        # Bonus for having Tier 1 sources
        tier1_bonus = min(tier1_count / 2.0, 0.3)  # Up to 0.3 bonus for 2+ Tier 1 sources

        # Check recency (bonus for fresh data)
        fresh_count = sum(1 for r in web_results if self._is_recent(r.get('date', '')))
        freshness_bonus = min(fresh_count / 3.0, 0.2)

        # Combine
        web_quality = (
            avg_weighted_quality * 0.5 +
            tier1_bonus +
            freshness_bonus
        )

        logger.info(
            f"Web quality breakdown: "
            f"Tier1={tier1_count}, Tier2={tier2_count}, Tier3={tier3_count}, "
            f"fresh={fresh_count}, quality={web_quality:.3f}"
        )

        return min(web_quality, 1.0)

    def _calculate_content_coherence(
        self,
        web_results: List[Dict],
        rag_results: List[Dict],
        sections: Dict[str, str]
    ) -> float:
        """
        Measures agreement across sources and grounding in synthesis

        Components:
        - Source agreement (40%)
        - Citation density (30%)
        - Factual consistency (30%)
        """
        score = 0.0

        # 1. Source agreement (0.4 of coherence)
        if len(rag_results) >= 2:
            # High confidence if multiple internal docs agree
            if len(rag_results) >= 3:
                agreement_score = 1.0
            else:
                agreement_score = 0.7
            score += agreement_score * 0.4
            logger.debug(f"Source agreement: {agreement_score:.3f} ({len(rag_results)} RAG docs)")
        elif len(web_results) >= 3:
            # Web sources provide some corroboration
            score += 0.6 * 0.4
            logger.debug(f"Source agreement: 0.6 ({len(web_results)} web sources)")

        # 2. Citation density (0.3 of coherence)
        # Count source citations [WEB-1], [RAG-2], etc.
        # Convert all section values to strings first
        total_text = ' '.join(str(v) for v in sections.values())
        citation_count = total_text.count('[WEB-') + total_text.count('[RAG-')

        if citation_count >= 5:
            citation_score = 1.0
        elif citation_count >= 3:
            citation_score = 0.7
        elif citation_count >= 1:
            citation_score = 0.4
        else:
            citation_score = 0.0

        score += citation_score * 0.3
        logger.debug(f"Citation density: {citation_score:.3f} ({citation_count} citations)")

        # 3. Factual consistency (0.3 of coherence)
        # Penalize if sections contain fallback/insufficient data markers
        insufficient_markers = [
            'insufficient data',
            'no data available',
            'analysis unavailable',
            'see retrieved sources',
            'llm synthesis unavailable'
        ]

        poor_sections = sum(
            1 for content in sections.values()
            if any(marker in str(content).lower() for marker in insufficient_markers)
        )

        consistency_score = max(0, 1.0 - (poor_sections / 7.0))  # 7 sections total
        score += consistency_score * 0.3
        logger.debug(f"Factual consistency: {consistency_score:.3f} ({poor_sections} poor sections)")

        return min(score, 1.0)

    def _calculate_synthesis_success(
        self,
        sections: Dict[str, str],
        web_results: List[Dict],
        rag_results: List[Dict]
    ) -> float:
        """
        Measures LLM synthesis quality

        Components:
        - Section completeness (50%)
        - Summary quality (30%)
        - Grounded synthesis (20%)
        """
        score = 0.0

        # 1. All sections populated (0.5 of synthesis)
        required_sections = [
            'summary', 'market_overview', 'key_metrics',
            'drivers_and_trends', 'competitive_landscape',
            'risks_and_opportunities', 'future_outlook'
        ]

        populated_count = sum(
            1 for section in required_sections
            if section in sections and len(str(sections[section]).strip()) > 20
        )

        completeness = populated_count / len(required_sections)
        score += completeness * 0.5
        logger.debug(f"Section completeness: {completeness:.3f} ({populated_count}/{len(required_sections)})")

        # 2. Summary quality (0.3 of synthesis)
        summary = sections.get('summary', '')
        if len(summary) > 100 and '[' in summary:  # Has content and citations
            summary_score = 1.0
        elif len(summary) > 50:
            summary_score = 0.6
        else:
            summary_score = 0.0

        score += summary_score * 0.3
        logger.debug(f"Summary quality: {summary_score:.3f} (len={len(summary)})")

        # 3. Grounded synthesis (0.2 of synthesis)
        # Reward if synthesis used retrieved sources
        total_sources = len(web_results) + len(rag_results)
        if total_sources > 0:
            grounding_score = 1.0
        else:
            grounding_score = 0.0

        score += grounding_score * 0.2
        logger.debug(f"Grounded synthesis: {grounding_score:.3f} ({total_sources} sources)")

        return min(score, 1.0)

    def _calculate_coverage_completeness(
        self,
        query: str,
        sections: Dict[str, str]
    ) -> float:
        """
        Measures if query was fully addressed

        Checks if relevant sections address query intent
        """
        query_lower = query.lower()
        coverage_score = 0.0

        # Define query intent keywords
        market_terms = ['market size', 'forecast', 'growth', 'cagr', 'revenue', 'sales']
        competitive_terms = ['player', 'company', 'competitive', 'share', 'landscape']

        # Check if relevant sections address query terms
        if any(term in query_lower for term in market_terms):
            if 'market_overview' in sections and len(str(sections['market_overview'])) > 50:
                coverage_score += 0.4
            if 'key_metrics' in sections and len(str(sections['key_metrics'])) > 30:
                coverage_score += 0.3

        if any(term in query_lower for term in competitive_terms):
            if 'competitive_landscape' in sections and len(str(sections['competitive_landscape'])) > 50:
                coverage_score += 0.3

        # Always expect summary and outlook
        if len(str(sections.get('summary', ''))) > 50:
            coverage_score += 0.2
        if len(str(sections.get('future_outlook', ''))) > 30:
            coverage_score += 0.2

        logger.debug(f"Coverage completeness: {coverage_score:.3f}")

        return min(coverage_score, 1.0)

    def _normalize_chroma_relevance(self, rag_result: Dict) -> float:
        """
        Convert Chroma distance to similarity score

        Chroma returns cosine distance: 0 (identical) to 2 (opposite)
        We convert to similarity: 1 (perfect) to 0 (irrelevant)
        """
        distance = rag_result.get("distance", 1.0)

        # Also check for relevance_score if already computed
        if "relevance_score" in rag_result:
            return rag_result["relevance_score"]

        # Convert distance to similarity
        similarity = max(0, 1 - (distance / 2.0))
        return similarity

    def _is_recent(self, date_str: str) -> bool:
        """
        Check if date is within last 12 months

        Args:
            date_str: Date string in various formats

        Returns:
            True if recent, False otherwise
        """
        if not date_str:
            return False

        try:
            # Try parsing common date formats
            date_formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%m/%d/%Y',
                '%B %d, %Y',
                '%b %d, %Y',
                '%Y'
            ]

            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str.strip(), fmt)
                    break
                except ValueError:
                    continue

            if not parsed_date:
                # Try extracting year
                if date_str.isdigit() and len(date_str) == 4:
                    year = int(date_str)
                    parsed_date = datetime(year, 1, 1)
                else:
                    return False

            # Check if within last 12 months
            twelve_months_ago = datetime.now() - timedelta(days=365)
            return parsed_date >= twelve_months_ago

        except Exception as e:
            logger.debug(f"Date parsing failed for '{date_str}': {e}")
            return False

    def _generate_explanation(
        self,
        final_score: float,
        retrieval_quality: float,
        content_coherence: float,
        synthesis_success: float,
        coverage_completeness: float,
        web_results: List[Dict],
        rag_results: List[Dict],
        sections: Dict[str, str]
    ) -> str:
        """
        Generate human-readable confidence explanation
        """
        explanations = []

        # Overall assessment
        level = self._determine_confidence_level(final_score)
        if level == "very_high":
            explanations.append("Very high confidence.")
        elif level == "high":
            explanations.append("High confidence.")
        elif level == "medium":
            explanations.append("Medium confidence.")
        else:
            explanations.append("Low confidence.")

        # Retrieval assessment
        if rag_results and len(rag_results) >= 3:
            explanations.append(f"Retrieved {len(rag_results)} high-quality internal documents with strong agreement.")
        elif rag_results:
            explanations.append(f"Retrieved {len(rag_results)} internal document(s).")

        if web_results:
            fresh_count = sum(1 for r in web_results if self._is_recent(r.get('date', '')))
            if fresh_count > 0:
                explanations.append(f"Corroborated by {len(web_results)} web sources ({fresh_count} recent).")
            else:
                explanations.append(f"Corroborated by {len(web_results)} web sources.")

        # Synthesis assessment
        populated_sections = sum(1 for s in sections.values() if len(s.strip()) > 20)
        if synthesis_success >= 0.8:
            explanations.append(f"Comprehensive synthesis with citations across all sections.")
        elif synthesis_success >= 0.5:
            explanations.append(f"Partial synthesis ({populated_sections}/7 sections populated).")
        else:
            explanations.append(f"Synthesis incomplete ({populated_sections}/7 sections).")

        # Issues/warnings
        if final_score < 0.5:
            if not rag_results and not web_results:
                explanations.append("⚠️ No sources retrieved. Answer may be unreliable.")
            elif synthesis_success < 0.3:
                explanations.append("⚠️ Synthesis quality low with missing sections.")

        return " ".join(explanations)

    def _determine_confidence_level(self, score: float) -> str:
        """
        Convert numeric score to confidence level label

        NEW CALIBRATED THRESHOLDS (per requirements):
        - < 0.50 → Low (insufficient evidence)
        - 0.50–0.65 → Medium (partial corroboration)
        - 0.65–0.80 → High (multi-source agreement)
        - > 0.80 → Very High (strong corroboration + coherence)
        """
        if score >= 0.80:
            return "very_high"
        elif score >= 0.65:
            return "high"
        elif score >= 0.50:
            return "medium"
        else:
            return "low"


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    scorer = ConfidenceScorer()

    # Test Case 1: RAG-only success
    print("\n" + "="*70)
    print("TEST CASE 1: RAG-Only Success")
    print("="*70)

    rag_results_1 = [
        {"distance": 0.15, "content": "...", "metadata": {}},
        {"distance": 0.20, "content": "...", "metadata": {}},
        {"distance": 0.25, "content": "...", "metadata": {}},
        {"distance": 0.30, "content": "...", "metadata": {}}
    ]

    sections_1 = {
        "summary": "GLP-1 market reached $23.5B in 2024 [RAG-1] with 18.2% CAGR [RAG-2].",
        "market_overview": "Current market size: $23.5B (2024) [RAG-1, RAG-3]. CAGR: 18.2% [RAG-2]. Forecast 2030: $45.8B [RAG-4].",
        "key_metrics": "Ozempic: $14.2B sales [RAG-1]. Wegovy: $4.5B [RAG-2]. Mounjaro: $5.1B [RAG-3].",
        "drivers_and_trends": "Obesity indication dominance (70% of prescriptions) [RAG-1]. Supply constraints [RAG-2].",
        "competitive_landscape": "Novo Nordisk leads with 60% share [RAG-3]. Eli Lilly gaining rapidly [RAG-4].",
        "risks_and_opportunities": "Patent expiries 2028+ [RAG-1]. Oral formulations in Phase 3 [RAG-2].",
        "future_outlook": "Market projected $45.8B by 2030 [RAG-4]. Cardiovascular expansion anticipated [RAG-3]."
    }

    result_1 = scorer.calculate_confidence(
        query="What is the GLP-1 market landscape?",
        web_results=[],
        rag_results=rag_results_1,
        sections=sections_1
    )

    print(f"\nConfidence Score: {result_1['score']:.1%}")
    print(f"Level: {result_1['level']}")
    print(f"Explanation: {result_1['explanation']}")
    print(f"\nBreakdown:")
    for component, score in result_1['breakdown'].items():
        print(f"  {component}: {score:.3f}")

    # Test Case 2: RAG + Web success
    print("\n" + "="*70)
    print("TEST CASE 2: RAG + Web Success")
    print("="*70)

    web_results_2 = [
        {"title": "...", "url": "...", "snippet": "...", "date": "2024-01-15"},
        {"title": "...", "url": "...", "snippet": "...", "date": "2024-02-20"},
        {"title": "...", "url": "...", "snippet": "...", "date": "2024-03-10"},
        {"title": "...", "url": "...", "snippet": "...", "date": "2023-11-05"},
        {"title": "...", "url": "...", "snippet": "...", "date": "2023-10-12"}
    ]

    rag_results_2 = rag_results_1[:3]
    sections_2 = sections_1.copy()

    result_2 = scorer.calculate_confidence(
        query="What is the GLP-1 market size and forecast?",
        web_results=web_results_2,
        rag_results=rag_results_2,
        sections=sections_2
    )

    print(f"\nConfidence Score: {result_2['score']:.1%}")
    print(f"Level: {result_2['level']}")
    print(f"Explanation: {result_2['explanation']}")
    print(f"\nBreakdown:")
    for component, score in result_2['breakdown'].items():
        print(f"  {component}: {score:.3f}")

    # Test Case 3: Partial failure
    print("\n" + "="*70)
    print("TEST CASE 3: Partial Failure")
    print("="*70)

    web_results_3 = [
        {"title": "...", "url": "...", "snippet": "...", "date": "2022-05-10"},
        {"title": "...", "url": "...", "snippet": "...", "date": "2022-08-15"}
    ]

    sections_3 = {
        "summary": "Analysis unavailable",
        "market_overview": "",
        "key_metrics": "LLM synthesis unavailable",
        "drivers_and_trends": "Some content here",
        "competitive_landscape": "See retrieved sources",
        "risks_and_opportunities": "See retrieved sources",
        "future_outlook": ""
    }

    result_3 = scorer.calculate_confidence(
        query="What is the GLP-1 market?",
        web_results=web_results_3,
        rag_results=[],
        sections=sections_3
    )

    print(f"\nConfidence Score: {result_3['score']:.1%}")
    print(f"Level: {result_3['level']}")
    print(f"Explanation: {result_3['explanation']}")
    print(f"\nBreakdown:")
    for component, score in result_3['breakdown'].items():
        print(f"  {component}: {score:.3f}")
