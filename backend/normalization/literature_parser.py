"""
Literature Evidence Parser

Parses LiteratureAgent output into normalized AKGP EvidenceNode objects.

INPUT: LiteratureAgent.process() output
OUTPUT: List[NormalizedEvidence]

DETERMINISTIC RULES:
- Extract drug from publication titles/abstracts, disease from same
- Polarity based on publication type:
  * Meta-analysis/Systematic review → SUPPORTS (strong evidence)
  * RCT/Clinical study → SUPPORTS (moderate evidence)
  * Case study/Review → SUGGESTS (weak evidence)
  * Default → SUGGESTS
- Quality based on publication type (Meta-analysis=HIGH, RCT=MEDIUM, Other=LOW)
- Reject publications missing drug OR disease
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
    determine_quality_from_publication_type,
    get_utc_timestamp,
    Polarity
)

logger = logging.getLogger(__name__)


def parse_literature_evidence(agent_output: Dict[str, Any]) -> List[NormalizedEvidence]:
    """
    Parse LiteratureAgent output into normalized evidence

    Args:
        agent_output: Output from LiteratureAgent.process()
            Expected structure:
            {
                "query": str,
                "summary": str,
                "comprehensive_summary": str,
                "publications": [
                    {
                        "pmid": str,
                        "title": str,
                        "abstract": str,
                        "authors": [str, ...],
                        "journal": str,
                        "year": str,
                        "url": str
                    },
                    ...
                ],
                "total_publications": int,
                "confidence_score": float,
                "agent_id": "literature"
            }

    Returns:
        List of NormalizedEvidence objects (one per publication)
        Empty list if no valid publications found

    Raises:
        ParsingRejection: If critical fields are missing
    """
    logger.info("Parsing LiteratureAgent output into normalized evidence")

    # Validate required top-level fields
    try:
        validate_required_fields(agent_output, ["query", "publications"])
    except ParsingRejection as e:
        logger.error(f"LiteratureAgent output missing required fields: {e}")
        raise

    publications = agent_output.get("publications", [])

    if not publications:
        logger.warning("No publications found in LiteratureAgent output")
        return []

    logger.info(f"Processing {len(publications)} publications")

    normalized_evidence = []

    for pub in publications:
        try:
            evidence = _parse_single_publication(pub)
            normalized_evidence.append(evidence)
            logger.debug(f"Successfully parsed publication: {evidence.evidence_node.raw_reference}")
        except ParsingRejection as e:
            # Expected - some publications may not have drug/disease
            logger.debug(f"Skipping publication: {e}")
            continue
        except Exception as e:
            # Unexpected error - log but continue
            logger.error(f"Unexpected error parsing publication: {e}", exc_info=True)
            continue

    logger.info(f"Successfully normalized {len(normalized_evidence)} of {len(publications)} publications")

    return normalized_evidence


def _parse_single_publication(pub: Dict[str, Any]) -> NormalizedEvidence:
    """
    Parse a single publication into NormalizedEvidence

    Args:
        pub: Single publication from LiteratureAgent output

    Returns:
        NormalizedEvidence object

    Raises:
        ParsingRejection: If publication cannot be parsed
    """
    # --- EXTRACT PMID (for raw_reference) ---
    pmid = pub.get("pmid", "")
    if not pmid:
        raise ParsingRejection("Missing PMID")

    # --- EXTRACT TITLE AND ABSTRACT ---
    title = pub.get("title", "")
    abstract = pub.get("abstract", "")

    # Combine title and abstract for entity extraction
    combined_text = f"{title} {abstract}"

    if not combined_text.strip():
        raise ParsingRejection(f"Publication {pmid}: No title or abstract")

    # --- EXTRACT DRUG MENTIONS ---
    drug_mentions = extract_drug_mentions(combined_text)

    if not drug_mentions:
        raise ParsingRejection(f"Publication {pmid}: No drug mentions found")

    primary_drug = drug_mentions[0]

    # --- EXTRACT DISEASE MENTIONS ---
    disease_mentions = extract_disease_mentions(combined_text)

    if not disease_mentions:
        raise ParsingRejection(f"Publication {pmid}: No disease mentions found")

    primary_disease = disease_mentions[0]

    # --- GENERATE CANONICAL IDS ---
    try:
        drug_id = generate_canonical_id(primary_drug, "drug")
        disease_id = generate_canonical_id(primary_disease, "disease")
    except ValueError as e:
        raise ParsingRejection(f"Publication {pmid}: Cannot generate canonical ID: {e}")

    # --- DETERMINE PUBLICATION TYPE (from title/abstract keywords) ---
    pub_type = _infer_publication_type(combined_text)

    # --- DETERMINE QUALITY ---
    quality = determine_quality_from_publication_type(pub_type)

    # --- DETERMINE POLARITY ---
    polarity = _determine_literature_polarity(pub_type, combined_text)

    # --- EXTRACT AUTHORS AND JOURNAL ---
    authors = pub.get("authors", [])
    author_str = ", ".join(authors[:3]) if authors else "Unknown Authors"

    journal = pub.get("journal", "Unknown Journal")
    year = pub.get("year", "Unknown Year")

    # --- CREATE SUMMARY ---
    summary_text = f"{author_str} et al. ({year}). {title[:200]}"

    # Ensure summary is non-empty
    if not summary_text.strip():
        summary_text = f"Publication {pmid}: {primary_drug} in {primary_disease}"

    # --- DETERMINE CONFIDENCE ---
    # Higher confidence for systematic reviews/meta-analyses
    confidence = _determine_literature_confidence(pub_type)

    # --- CREATE EVIDENCE NODE ---
    timestamp = get_utc_timestamp()

    evidence_node = EvidenceNode(
        name=f"Publication {pmid}",
        source="PubMed",
        agent_name="Literature Agent",
        agent_id="literature",
        api_source="PubMed API",
        raw_reference=f"PMID:{pmid}",
        extraction_timestamp=timestamp,
        source_type=SourceType.LITERATURE,
        quality=quality,
        confidence_score=confidence,
        summary=summary_text,
        full_text=abstract,  # Store abstract as full_text
        metadata={
            "pmid": pmid,
            "authors": authors,
            "journal": journal,
            "year": year,
            "publication_type": pub_type,
            "drug_mentions": drug_mentions,
            "disease_mentions": disease_mentions
        }
    )

    # --- CREATE NORMALIZED EVIDENCE ---
    return NormalizedEvidence(
        evidence_node=evidence_node,
        drug_id=drug_id,
        disease_id=disease_id,
        polarity=polarity
    )


def _infer_publication_type(text: str) -> str:
    """
    Infer publication type from title/abstract keywords

    Returns: "meta-analysis", "systematic review", "rct", "clinical trial", "case study", "review", or "other"
    """
    text_lower = text.lower()

    if "meta-analysis" in text_lower or "meta analysis" in text_lower:
        return "meta-analysis"
    elif "systematic review" in text_lower:
        return "systematic review"
    elif any(term in text_lower for term in ["randomized controlled trial", "rct", "randomized"]):
        return "rct"
    elif "clinical trial" in text_lower or "clinical study" in text_lower:
        return "clinical trial"
    elif "case study" in text_lower or "case report" in text_lower:
        return "case study"
    elif "review" in text_lower:
        return "review"
    else:
        return "other"


def _determine_literature_polarity(pub_type: str, text: str) -> str:
    """
    Determine polarity from publication type and content

    RULES:
    - Meta-analysis/Systematic review → SUPPORTS (strong evidence synthesis)
    - RCT/Clinical trial → SUPPORTS (experimental evidence)
    - Review/Case study/Other → SUGGESTS (weaker evidence)
    - Negative language ("failed", "ineffective") → CONTRADICTS

    Args:
        pub_type: Inferred publication type
        text: Combined title + abstract

    Returns:
        Polarity string (SUPPORTS/CONTRADICTS/SUGGESTS)
    """
    text_lower = text.lower()

    # Check for negative language
    negative_terms = [
        "failed", "ineffective", "no effect", "no significant",
        "unsuccessful", "adverse", "contraindicated", "discontinued"
    ]

    if any(term in text_lower for term in negative_terms):
        return Polarity.CONTRADICTS

    # Strong evidence types → SUPPORTS
    if pub_type in ["meta-analysis", "systematic review", "rct", "clinical trial"]:
        return Polarity.SUPPORTS

    # Weaker evidence → SUGGESTS
    return Polarity.SUGGESTS


def _determine_literature_confidence(pub_type: str) -> float:
    """
    Determine confidence score from publication type

    RULES:
    - Meta-analysis → 0.9 (highest confidence)
    - Systematic review → 0.85
    - RCT → 0.8
    - Clinical trial → 0.75
    - Review → 0.6
    - Case study/Other → 0.5

    Args:
        pub_type: Inferred publication type

    Returns:
        Confidence score in [0.0, 1.0]
    """
    confidence_map = {
        "meta-analysis": 0.9,
        "systematic review": 0.85,
        "rct": 0.8,
        "clinical trial": 0.75,
        "review": 0.6,
        "case study": 0.5,
        "other": 0.5
    }

    return confidence_map.get(pub_type, 0.5)
