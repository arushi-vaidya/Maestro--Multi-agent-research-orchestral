"""
Conflict View - Conflict Explanation Façade

Provides frontend-safe access to conflict reasoning results.

CRITICAL CONSTRAINTS:
- READ-ONLY: Does NOT modify graph
- Does NOT trigger conflict computation
- Does NOT call agents
- ONLY exposes already-computed conflict analysis

Endpoints:
- GET /api/conflicts/explanation: Get conflict explanation for last query
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime
import logging

from api.views.cache import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conflicts", tags=["Conflicts"])


# ==============================================================================
# RESPONSE MODELS
# ==============================================================================

class EvidenceSummary(BaseModel):
    """
    Brief evidence summary for conflict explanation
    """
    evidence_id: str
    source: str
    agent_id: str
    quality: str
    confidence: float
    reference: str


class ConflictExplanationResponse(BaseModel):
    """
    Frontend-safe conflict explanation

    Provides human-readable explanation of detected conflicts.
    """
    has_conflict: bool
    severity: Literal["LOW", "MEDIUM", "HIGH", "NONE"]
    dominant_evidence_id: Optional[str] = None
    explanation: str
    supporting_evidence: List[EvidenceSummary]
    contradicting_evidence: List[EvidenceSummary]
    temporal_reasoning: Optional[str] = None  # Why newer evidence dominates
    evidence_counts: Dict[str, int]  # supports, contradicts, suggests

    class Config:
        json_schema_extra = {
            "example": {
                "has_conflict": True,
                "severity": "MEDIUM",
                "dominant_evidence_id": "ev_12345",
                "explanation": "Moderate conflict detected: 8 evidence pieces support the hypothesis, but 3 recent studies contradict. Newer evidence (Phase 3 trial NCT05123456) shows lower efficacy than earlier Phase 2 results.",
                "supporting_evidence": [
                    {
                        "evidence_id": "ev_11111",
                        "source": "ClinicalTrials.gov",
                        "agent_id": "clinical",
                        "quality": "HIGH",
                        "confidence": 0.9,
                        "reference": "NCT05123456"
                    }
                ],
                "contradicting_evidence": [
                    {
                        "evidence_id": "ev_22222",
                        "source": "PubMed",
                        "agent_id": "literature",
                        "quality": "MEDIUM",
                        "confidence": 0.7,
                        "reference": "PMID: 34567890"
                    }
                ],
                "temporal_reasoning": "Recent Phase 3 trial (2024) contradicts earlier Phase 2 results (2022)",
                "evidence_counts": {
                    "supports": 8,
                    "contradicts": 3,
                    "suggests": 5
                }
            }
        }


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.get("/explanation", response_model=ConflictExplanationResponse)
def get_conflict_explanation(response: Response):
    """
    Get conflict explanation for last queried drug-disease pair

    This endpoint:
    - Reads conflict analysis from last /api/query execution
    - Does NOT recompute conflicts
    - Does NOT trigger agents
    - Does NOT modify graph

    Returns:
        ConflictExplanationResponse with conflict details and reasoning

    Raises:
        404: No conflict data available (no query executed yet)
        500: Error reading cached results
    """
    try:
        # Prevent caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        cache = get_cache()

        # If no conflict data yet, return empty-but-valid response to avoid 404s on polling
        if cache.is_empty():
            return ConflictExplanationResponse(
                has_conflict=False,
                severity="NONE",
                dominant_evidence_id=None,
                explanation="No conflict data available yet. Run a query first.",
                supporting_evidence=[],
                contradicting_evidence=[],
                temporal_reasoning=None,
                evidence_counts={"supports": 0, "contradicts": 0, "suggests": 0},
            )

        # Get ROS result which contains conflict summary
        ros_result = cache.get_last_ros_result()

        if ros_result is None:
            # Try to extract from last response
            last_response = cache.get_last_response()
            if last_response and 'ros_results' in last_response:
                ros_result = last_response['ros_results']
            else:
                return ConflictExplanationResponse(
                    has_conflict=False,
                    severity="NONE",
                    dominant_evidence_id=None,
                    explanation="Conflict analysis not available for last query.",
                    supporting_evidence=[],
                    contradicting_evidence=[],
                    temporal_reasoning=None,
                    evidence_counts={"supports": 0, "contradicts": 0, "suggests": 0},
                )

        # Extract conflict summary
        conflict_summary = ros_result.get('conflict_summary', {})

        if not conflict_summary:
            # No conflict detected - return empty but valid response
            return ConflictExplanationResponse(
                has_conflict=False,
                severity="NONE",
                dominant_evidence_id=None,
                explanation="No conflicts detected. All evidence is consistent.",
                supporting_evidence=[],
                contradicting_evidence=[],
                temporal_reasoning=None,
                evidence_counts={"supports": 0, "contradicts": 0, "suggests": 0}
            )

        # Extract fields from conflict summary
        has_conflict = conflict_summary.get('has_conflict', False)
        severity = conflict_summary.get('severity', 'NONE')
        if severity is None:
            severity = "NONE"

        # Extract dominant evidence
        dominant_evidence = conflict_summary.get('dominant_evidence', {})
        dominant_evidence_id = dominant_evidence.get('evidence_id') if dominant_evidence else None

        # Extract explanation
        explanation = conflict_summary.get('summary', 'No conflict explanation available')

        # Extract temporal reasoning
        temporal_reasoning = conflict_summary.get('temporal_explanation')

        # Extract evidence lists
        supporting_raw = conflict_summary.get('supporting_evidence', [])
        contradicting_raw = conflict_summary.get('contradicting_evidence', [])

        # Convert to frontend format
        supporting_evidence = [
            EvidenceSummary(
                evidence_id=ev.get('evidence_id', ev.get('id', 'unknown')),
                source=ev.get('api_source', ev.get('source', 'Unknown')),
                agent_id=ev.get('agent_id', 'unknown'),
                quality=ev.get('quality', 'MEDIUM').upper(),
                confidence=ev.get('confidence_score', ev.get('confidence', 0.5)),
                reference=ev.get('raw_reference', ev.get('reference', 'Unknown'))
            )
            for ev in supporting_raw
        ]

        contradicting_evidence = [
            EvidenceSummary(
                evidence_id=ev.get('evidence_id', ev.get('id', 'unknown')),
                source=ev.get('api_source', ev.get('source', 'Unknown')),
                agent_id=ev.get('agent_id', 'unknown'),
                quality=ev.get('quality', 'MEDIUM').upper(),
                confidence=ev.get('confidence_score', ev.get('confidence', 0.5)),
                reference=ev.get('raw_reference', ev.get('reference', 'Unknown'))
            )
            for ev in contradicting_raw
        ]

        # Extract evidence counts
        evidence_counts = conflict_summary.get('evidence_count', {})
        if not evidence_counts:
            # Calculate from evidence lists
            evidence_counts = {
                "supports": len(supporting_raw),
                "contradicts": len(contradicting_raw),
                "suggests": 0
            }

        logger.info(f"✅ Conflict explanation: has_conflict={has_conflict}, severity={severity}")

        return ConflictExplanationResponse(
            has_conflict=has_conflict,
            severity=severity,
            dominant_evidence_id=dominant_evidence_id,
            explanation=explanation,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            temporal_reasoning=temporal_reasoning,
            evidence_counts=evidence_counts
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conflict explanation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conflict explanation: {str(e)}"
        )
