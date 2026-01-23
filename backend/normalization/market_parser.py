"""
Market Evidence Parser

Parses MarketAgent output into normalized AKGP EvidenceNode objects.

INPUT: MarketAgent.process() output
OUTPUT: List[NormalizedEvidence]

DETERMINISTIC RULES:
- Extract drug from query/sections, disease from query/sections
- Polarity: ALL market signals → SUGGESTS (forecasts are speculative)
- Quality: ALL market signals → LOW (market data ≠ clinical evidence)
- Create ONE evidence node per query (aggregate market intelligence)
- Reject if no drug OR disease can be extracted
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

from akgp.schema import EvidenceNode, SourceType, EvidenceQuality
from normalization.common import (
    NormalizedEvidence,
    ParsingRejection,
    generate_canonical_id,
    extract_drug_mentions,
    extract_disease_mentions,
    validate_required_fields,
    validate_confidence,
    get_utc_timestamp,
    Polarity
)

logger = logging.getLogger(__name__)


def parse_market_evidence(agent_output: Dict[str, Any]) -> List[NormalizedEvidence]:
    """
    Parse MarketAgent output into normalized evidence

    Args:
        agent_output: Output from MarketAgent.process()
            Expected structure:
            {
                "agentId": "market",
                "query": str,
                "sections": {
                    "summary": str,
                    "market_overview": str,
                    "key_metrics": str,
                    ...
                },
                "confidence": {...},
                "confidence_score": float,
                "web_results": [...],
                "rag_results": [...]
            }

    Returns:
        List of NormalizedEvidence objects (typically ONE per query)
        Empty list if no valid evidence found

    Raises:
        ParsingRejection: If critical fields are missing
    """
    logger.info("Parsing MarketAgent output into normalized evidence")

    # Validate required top-level fields
    try:
        validate_required_fields(agent_output, ["agentId", "query", "sections"])
    except ParsingRejection as e:
        logger.error(f"MarketAgent output missing required fields: {e}")
        raise

    # Extract query
    query = agent_output.get("query", "")
    if not query.strip():
        raise ParsingRejection("Query is empty")

    # Extract sections
    sections = agent_output.get("sections", {})
    if not sections:
        raise ParsingRejection("No sections found in MarketAgent output")

    # Combine query + sections for entity extraction
    combined_text = (
        f"{query} "
        f"{sections.get('summary', '')} "
        f"{sections.get('market_overview', '')} "
        f"{sections.get('key_metrics', '')}"
    )

    # --- EXTRACT DRUG MENTIONS ---
    drug_mentions = extract_drug_mentions(combined_text)

    if not drug_mentions:
        raise ParsingRejection(f"No drug mentions found in query or sections")

    primary_drug = drug_mentions[0]

    # --- EXTRACT DISEASE MENTIONS ---
    disease_mentions = extract_disease_mentions(combined_text)

    if not disease_mentions:
        raise ParsingRejection(f"No disease mentions found in query or sections")

    primary_disease = disease_mentions[0]

    # --- GENERATE CANONICAL IDS ---
    try:
        drug_id = generate_canonical_id(primary_drug, "drug")
        disease_id = generate_canonical_id(primary_disease, "disease")
    except ValueError as e:
        raise ParsingRejection(f"Cannot generate canonical ID: {e}")

    # --- DETERMINE QUALITY ---
    # Market signals are LOW quality (not clinical evidence)
    quality = EvidenceQuality.LOW

    # --- DETERMINE POLARITY ---
    # ALL market signals are SUGGESTS (forecasts are speculative)
    polarity = Polarity.SUGGESTS

    # --- EXTRACT CONFIDENCE ---
    confidence_score = agent_output.get("confidence_score", 0.5)
    try:
        confidence = validate_confidence(confidence_score)
    except ParsingRejection:
        confidence = 0.5  # Default if invalid

    # --- CREATE SUMMARY ---
    summary_text = sections.get("summary", "")
    if not summary_text.strip():
        # Fallback to market_overview
        summary_text = sections.get("market_overview", "")

    if not summary_text.strip():
        # Final fallback
        summary_text = f"Market intelligence for {primary_drug} in {primary_disease}"

    # --- EXTRACT SOURCES FOR RAW_REFERENCE ---
    web_results = agent_output.get("web_results", [])
    rag_results = agent_output.get("rag_results", [])

    # Create raw_reference from source URLs
    web_urls = [r.get("url", "") for r in web_results[:3] if r.get("url")]
    raw_reference = ", ".join(web_urls) if web_urls else "Market Intelligence Query"

    # --- CREATE EVIDENCE NODE ---
    timestamp = get_utc_timestamp()

    evidence_node = EvidenceNode(
        name=f"Market Intelligence: {primary_drug}",
        source="Market Intelligence (Web + RAG)",
        agent_name="Market Agent",
        agent_id="market",
        api_source="Web Search + Internal RAG",
        raw_reference=raw_reference,
        extraction_timestamp=timestamp,
        source_type=SourceType.MARKET,
        quality=quality,
        confidence_score=confidence,
        summary=summary_text,
        full_text=None,  # Could store all sections here if needed
        metadata={
            "query": query,
            "web_sources_count": len(web_results),
            "rag_sources_count": len(rag_results),
            "drug_mentions": drug_mentions,
            "disease_mentions": disease_mentions,
            "sections": sections
        }
    )

    # --- CREATE NORMALIZED EVIDENCE ---
    normalized_evidence = NormalizedEvidence(
        evidence_node=evidence_node,
        drug_id=drug_id,
        disease_id=disease_id,
        polarity=polarity
    )

    logger.info(f"Successfully normalized market evidence for {primary_drug} / {primary_disease}")

    # Return as list (market evidence is typically one aggregate per query)
    return [normalized_evidence]
