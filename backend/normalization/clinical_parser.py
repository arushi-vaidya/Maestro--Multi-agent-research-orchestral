"""
Clinical Evidence Parser

Parses ClinicalAgent output into normalized AKGP EvidenceNode objects.

INPUT: ClinicalAgent.process() output
OUTPUT: List[NormalizedEvidence]

DETERMINISTIC RULES:
- Extract drug from interventions[], disease from conditions[]
- Polarity based on trial status/phase:
  * COMPLETED Phase 3/4 → SUPPORTS (successful clinical evidence)
  * RECRUITING/ACTIVE Phase 3/4 → SUGGESTS (promising but ongoing)
  * Phase 1/2 → SUGGESTS (early evidence)
  * TERMINATED/WITHDRAWN → CONTRADICTS (failed trial)
- Quality based on phase (Phase 3/4=HIGH, Phase 2=MEDIUM, Phase 1=LOW)
- Reject trials missing drug OR disease
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from akgp.schema import EvidenceNode, SourceType, EvidenceQuality
from normalization.common import (
    NormalizedEvidence,
    ParsingRejection,
    generate_canonical_id,
    normalize_entity_name,
    validate_confidence,
    validate_required_fields,
    determine_quality_from_phase,
    get_utc_timestamp,
    Polarity
)

logger = logging.getLogger(__name__)


def parse_clinical_evidence(agent_output: Dict[str, Any]) -> List[NormalizedEvidence]:
    """
    Parse ClinicalAgent output into normalized evidence

    Args:
        agent_output: Output from ClinicalAgent.process()
            Expected structure:
            {
                "summary": str,
                "comprehensive_summary": str,
                "trials": [{"nct_id": str, "title": str}, ...],
                "raw": {"studies": [...], "totalCount": int}
            }

    Returns:
        List of NormalizedEvidence objects (one per trial)
        Empty list if no valid trials found

    Raises:
        ParsingRejection: If critical fields are missing or output is malformed
    """
    logger.info("Parsing ClinicalAgent output into normalized evidence")

    # Validate required top-level fields
    try:
        validate_required_fields(agent_output, ["summary", "trials", "raw"])
    except ParsingRejection as e:
        logger.error(f"ClinicalAgent output missing required fields: {e}")
        raise

    # Extract raw trial data
    raw_data = agent_output.get("raw", {})
    studies = raw_data.get("studies", [])

    if not studies:
        logger.warning("No studies found in ClinicalAgent output")
        return []

    logger.info(f"Processing {len(studies)} clinical trials")

    normalized_evidence = []

    for study in studies:
        try:
            evidence = _parse_single_trial(study)
            normalized_evidence.append(evidence)
            logger.debug(f"Successfully parsed trial: {evidence.evidence_node.raw_reference}")
        except ParsingRejection as e:
            # Expected - some trials may not have drug/disease or be unparseable
            logger.debug(f"Skipping trial: {e}")
            continue
        except Exception as e:
            # Unexpected error - log but continue processing other trials
            logger.error(f"Unexpected error parsing trial: {e}", exc_info=True)
            continue

    logger.info(f"Successfully normalized {len(normalized_evidence)} of {len(studies)} trials")

    return normalized_evidence


def _parse_single_trial(study: Dict[str, Any]) -> NormalizedEvidence:
    """
    Parse a single clinical trial into NormalizedEvidence

    Args:
        study: Single study from ClinicalTrials.gov API response

    Returns:
        NormalizedEvidence object

    Raises:
        ParsingRejection: If trial cannot be parsed (missing drug/disease, etc.)
    """
    # Extract protocol section
    protocol = study.get("protocolSection", {})
    if not protocol:
        raise ParsingRejection("Missing protocolSection in trial data")

    # --- EXTRACT NCT ID (for raw_reference) ---
    id_module = protocol.get("identificationModule", {})
    nct_id = id_module.get("nctId", "")
    if not nct_id:
        raise ParsingRejection("Missing NCT ID")

    # --- EXTRACT INTERVENTIONS (DRUGS) ---
    arms_module = protocol.get("armsInterventionsModule", {})
    interventions = arms_module.get("interventions", [])

    drug_names = []
    for intervention in interventions:
        if intervention.get("type") == "DRUG":
            drug_name = intervention.get("name", "").strip()
            if drug_name:
                drug_names.append(drug_name)

    if not drug_names:
        raise ParsingRejection(f"Trial {nct_id}: No drug interventions found")

    # Use first drug (most trials have one primary intervention)
    primary_drug = drug_names[0]

    # --- EXTRACT CONDITIONS (DISEASES) ---
    conditions_module = protocol.get("conditionsModule", {})
    conditions = conditions_module.get("conditions", [])

    if not conditions:
        raise ParsingRejection(f"Trial {nct_id}: No conditions found")

    # Use first condition (primary indication)
    primary_disease = conditions[0].strip()

    # --- GENERATE CANONICAL IDS ---
    try:
        drug_id = generate_canonical_id(primary_drug, "drug")
        disease_id = generate_canonical_id(primary_disease, "disease")
    except ValueError as e:
        raise ParsingRejection(f"Trial {nct_id}: Cannot generate canonical ID: {e}")

    # --- EXTRACT PHASE (for quality and polarity) ---
    design_module = protocol.get("designModule", {})
    phases = design_module.get("phases", [])
    phase_str = phases[0] if phases else "UNKNOWN"

    # --- EXTRACT STATUS (for polarity) ---
    status_module = protocol.get("statusModule", {})
    status = status_module.get("overallStatus", "UNKNOWN")

    # --- DETERMINE QUALITY ---
    quality = determine_quality_from_phase(phase_str)

    # --- DETERMINE POLARITY ---
    polarity = _determine_clinical_polarity(phase_str, status)

    # --- EXTRACT SUMMARY ---
    desc_module = protocol.get("descriptionModule", {})
    brief_summary = desc_module.get("briefSummary", "")
    brief_title = id_module.get("briefTitle", "")

    summary_text = brief_summary or brief_title or f"Clinical trial {nct_id}"

    # Ensure summary is non-empty (Pydantic validation)
    if not summary_text.strip():
        summary_text = f"Clinical trial {nct_id} for {primary_drug} in {primary_disease}"

    # --- DETERMINE CONFIDENCE ---
    # Higher confidence for later-phase trials
    confidence = _determine_clinical_confidence(phase_str, status)

    # --- CREATE EVIDENCE NODE ---
    timestamp = get_utc_timestamp()

    evidence_node = EvidenceNode(
        name=f"Clinical Trial {nct_id}",
        source="ClinicalTrials.gov",
        agent_name="Clinical Agent",
        agent_id="clinical",
        api_source="ClinicalTrials.gov v2 API",
        raw_reference=nct_id,
        extraction_timestamp=timestamp,
        source_type=SourceType.CLINICAL,
        quality=quality,
        confidence_score=confidence,
        summary=summary_text,
        full_text=None,  # Could store full protocol here if needed
        metadata={
            "phase": phase_str,
            "status": status,
            "interventions": drug_names,
            "conditions": conditions
        }
    )

    # --- CREATE NORMALIZED EVIDENCE ---
    return NormalizedEvidence(
        evidence_node=evidence_node,
        drug_id=drug_id,
        disease_id=disease_id,
        polarity=polarity
    )


def _determine_clinical_polarity(phase: str, status: str) -> str:
    """
    Determine polarity (relationship type) from trial phase and status

    RULES:
    - COMPLETED Phase 3/4 → SUPPORTS (proven efficacy)
    - TERMINATED/WITHDRAWN → CONTRADICTS (failed trial)
    - All other cases → SUGGESTS (promising but not proven)

    Args:
        phase: Trial phase (e.g., "PHASE3", "PHASE2")
        status: Trial status (e.g., "COMPLETED", "RECRUITING")

    Returns:
        Polarity string (SUPPORTS/CONTRADICTS/SUGGESTS)
    """
    phase_lower = phase.lower() if phase else ""
    status_lower = status.lower() if status else ""

    # Failed trials → CONTRADICTS
    if any(term in status_lower for term in ['terminated', 'withdrawn', 'suspended']):
        return Polarity.CONTRADICTS

    # Completed late-stage trials → SUPPORTS
    if 'completed' in status_lower:
        if any(p in phase_lower for p in ['phase 3', 'phase3', 'phase 4', 'phase4']):
            return Polarity.SUPPORTS

    # All other cases → SUGGESTS (ongoing, early-phase, or unknown)
    return Polarity.SUGGESTS


def _determine_clinical_confidence(phase: str, status: str) -> float:
    """
    Determine confidence score from trial phase and status

    RULES:
    - Completed Phase 3/4 → 0.9 (high confidence)
    - Recruiting/Active Phase 3 → 0.7 (moderate-high)
    - Phase 2 → 0.6 (moderate)
    - Phase 1 → 0.4 (low-moderate)
    - Terminated → 0.3 (low, negative evidence)
    - Unknown → 0.5 (default)

    Args:
        phase: Trial phase string
        status: Trial status string

    Returns:
        Confidence score in [0.0, 1.0]
    """
    phase_lower = phase.lower() if phase else ""
    status_lower = status.lower() if status else ""

    # Terminated trials have low confidence
    if any(term in status_lower for term in ['terminated', 'withdrawn']):
        return 0.3

    # Completed trials have higher confidence
    if 'completed' in status_lower:
        if any(p in phase_lower for p in ['phase 3', 'phase3', 'phase 4', 'phase4']):
            return 0.9
        elif any(p in phase_lower for p in ['phase 2', 'phase2']):
            return 0.7
        elif any(p in phase_lower for p in ['phase 1', 'phase1']):
            return 0.5

    # Ongoing trials
    if any(p in phase_lower for p in ['phase 3', 'phase3', 'phase 4', 'phase4']):
        return 0.7
    elif any(p in phase_lower for p in ['phase 2', 'phase2']):
        return 0.6
    elif any(p in phase_lower for p in ['phase 1', 'phase1']):
        return 0.4

    # Default
    return 0.5
