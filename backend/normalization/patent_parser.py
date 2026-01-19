"""
Patent Evidence Parser

Parses PatentAgent output into normalized AKGP EvidenceNode objects.

INPUT: PatentAgent.process() output
OUTPUT: List[NormalizedEvidence]

DETERMINISTIC RULES:
- Extract drug from patent title/abstract, disease from claims/abstract
- Polarity:
  * Granted patents → SUGGESTS (patents are speculative IP, not proven efficacy)
  * Pending/filed → SUGGESTS (even more speculative)
  * All patents are SUGGESTS (patents ≠ clinical proof)
- Quality: Granted=MEDIUM, Pending/Unknown=LOW
- Reject patents missing drug OR disease
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
    determine_quality_from_patent_status,
    get_utc_timestamp,
    Polarity
)

logger = logging.getLogger(__name__)


def parse_patent_evidence(agent_output: Dict[str, Any]) -> List[NormalizedEvidence]:
    """
    Parse PatentAgent output into normalized evidence

    Args:
        agent_output: Output from PatentAgent.process()
            Expected structure:
            {
                "summary": str,
                "comprehensive_summary": str,
                "patents": [{"patent_number": str, "patent_title": str, ...}, ...],
                "landscape": {...},
                "fto_assessment": {...},
                "confidence_score": float
            }

    Returns:
        List of NormalizedEvidence objects (one per patent)
        Empty list if no valid patents found

    Raises:
        ParsingRejection: If critical fields are missing
    """
    logger.info("Parsing PatentAgent output into normalized evidence")

    # Validate required top-level fields
    try:
        validate_required_fields(agent_output, ["summary", "patents"])
    except ParsingRejection as e:
        logger.error(f"PatentAgent output missing required fields: {e}")
        raise

    patents = agent_output.get("patents", [])

    if not patents:
        logger.warning("No patents found in PatentAgent output")
        return []

    logger.info(f"Processing {len(patents)} patents")

    normalized_evidence = []

    for patent in patents:
        try:
            evidence = _parse_single_patent(patent)
            normalized_evidence.append(evidence)
            logger.debug(f"Successfully parsed patent: {evidence.evidence_node.raw_reference}")
        except ParsingRejection as e:
            # Expected - some patents may not have drug/disease
            logger.debug(f"Skipping patent: {e}")
            continue
        except Exception as e:
            # Unexpected error - log but continue
            logger.error(f"Unexpected error parsing patent: {e}", exc_info=True)
            continue

    logger.info(f"Successfully normalized {len(normalized_evidence)} of {len(patents)} patents")

    return normalized_evidence


def _parse_single_patent(patent: Dict[str, Any]) -> NormalizedEvidence:
    """
    Parse a single patent into NormalizedEvidence

    Args:
        patent: Single patent record from PatentAgent output

    Returns:
        NormalizedEvidence object

    Raises:
        ParsingRejection: If patent cannot be parsed
    """
    # --- EXTRACT PATENT NUMBER (for raw_reference) ---
    patent_number = patent.get("patent_number", "")
    if not patent_number:
        raise ParsingRejection("Missing patent_number")

    # --- EXTRACT TITLE AND ABSTRACT ---
    title = patent.get("patent_title", "")
    abstract = patent.get("patent_abstract", "")

    # Combine title and abstract for entity extraction
    combined_text = f"{title} {abstract}"

    if not combined_text.strip():
        raise ParsingRejection(f"Patent {patent_number}: No title or abstract")

    # --- EXTRACT DRUG MENTIONS ---
    drug_mentions = extract_drug_mentions(combined_text)

    if not drug_mentions:
        raise ParsingRejection(f"Patent {patent_number}: No drug mentions found in title/abstract")

    # Use first drug mention (most prominent)
    primary_drug = drug_mentions[0]

    # --- EXTRACT DISEASE MENTIONS ---
    disease_mentions = extract_disease_mentions(combined_text)

    if not disease_mentions:
        raise ParsingRejection(f"Patent {patent_number}: No disease mentions found in title/abstract")

    # Use first disease mention
    primary_disease = disease_mentions[0]

    # --- GENERATE CANONICAL IDS ---
    try:
        drug_id = generate_canonical_id(primary_drug, "drug")
        disease_id = generate_canonical_id(primary_disease, "disease")
    except ValueError as e:
        raise ParsingRejection(f"Patent {patent_number}: Cannot generate canonical ID: {e}")

    # --- DETERMINE QUALITY (from patent metadata) ---
    # Patents don't have explicit "status" in our data, but we can infer from metadata
    # For now, use patent_date as proxy: recent patents = granted (MEDIUM), others = LOW
    patent_date = patent.get("patent_date", "")

    # Simple heuristic: if we have a patent_date, assume it's granted
    quality = EvidenceQuality.MEDIUM if patent_date else EvidenceQuality.LOW

    # --- DETERMINE POLARITY ---
    # ALL patents are SUGGESTS (patents are speculative, not clinical proof)
    polarity = Polarity.SUGGESTS

    # --- EXTRACT ASSIGNEES (for metadata) ---
    assignees = patent.get("assignees", [])
    assignee_names = [a.get("assignee_organization", "") for a in assignees if a.get("assignee_organization")]

    # --- CREATE SUMMARY ---
    assignee_str = assignee_names[0] if assignee_names else "Unknown Assignee"
    summary_text = (
        f"Patent {patent_number} by {assignee_str}: "
        f"{title[:100] if title else abstract[:100]}"
    )

    # Ensure summary is non-empty
    if not summary_text.strip():
        summary_text = f"Patent {patent_number} for {primary_drug} in {primary_disease}"

    # --- DETERMINE CONFIDENCE ---
    # Patents have lower confidence than clinical trials (IP ≠ efficacy)
    # Granted patents = 0.5, pending/unknown = 0.3
    confidence = 0.5 if patent_date else 0.3

    # --- CREATE EVIDENCE NODE ---
    timestamp = get_utc_timestamp()

    evidence_node = EvidenceNode(
        name=f"Patent {patent_number}",
        source="Lens.org Patents API",
        agent_name="Patent Agent",
        agent_id="patent",
        api_source="Lens.org Patents API",
        raw_reference=patent_number,
        extraction_timestamp=timestamp,
        source_type=SourceType.PATENT,
        quality=quality,
        confidence_score=confidence,
        summary=summary_text,
        full_text=abstract,  # Store abstract as full_text
        metadata={
            "patent_date": patent_date,
            "assignees": assignee_names,
            "citations": patent.get("citedby_patent_count", 0),
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
