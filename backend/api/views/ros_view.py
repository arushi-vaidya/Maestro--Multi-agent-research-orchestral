"""
ROS View - Research Opportunity Scoring Façade

Provides frontend-safe access to ROS computation results.

CRITICAL CONSTRAINTS:
- READ-ONLY: Does NOT trigger ROS computation
- Does NOT call agents
- Does NOT modify AKGP graph
- ONLY exposes already-computed ROS results from last /api/query execution

Endpoint:
- GET /api/ros/latest: Get ROS score for last queried drug-disease pair
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Dict, Literal, Optional, Any
from datetime import datetime
import logging

from api.views.cache import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ros", tags=["ROS"])


# ==============================================================================
# RESPONSE MODELS
# ==============================================================================

class ROSViewResponse(BaseModel):
    """
    Frontend-safe ROS response

    Exposes ROS score breakdown in a clean, stable format for UI visualization.
    """
    drug: str
    disease: str
    ros_score: float
    confidence_level: Literal["LOW", "MEDIUM", "HIGH"]
    breakdown: Dict[str, float]  # evidence_strength, evidence_diversity, conflict_penalty, recency_boost, patent_risk_penalty
    conflict_penalty: float
    explanation: str
    metadata: Dict[str, Any]  # computation_timestamp, num_evidence, distinct_agents

    class Config:
        json_schema_extra = {
            "example": {
                "drug": "Semaglutide",
                "disease": "Type 2 Diabetes",
                "ros_score": 7.5,
                "confidence_level": "HIGH",
                "breakdown": {
                    "evidence_strength": 3.2,
                    "evidence_diversity": 2.0,
                    "conflict_penalty": -0.5,
                    "recency_boost": 1.8,
                    "patent_risk_penalty": -1.0
                },
                "conflict_penalty": -0.5,
                "explanation": "Strong evidence from 4 agents with minimal conflicts. Recent trials show positive outcomes. Moderate patent risk identified.",
                "metadata": {
                    "computation_timestamp": "2025-01-19T12:00:00Z",
                    "num_supporting_evidence": 12,
                    "num_contradicting_evidence": 2,
                    "distinct_agents": ["clinical", "market", "patent", "literature"]
                }
            }
        }


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.get("/latest", response_model=ROSViewResponse)
def get_latest_ros(response: Response):
    """
    Get ROS score for last queried drug-disease pair

    This endpoint:
    - Reads ROS results from last /api/query execution
    - Does NOT recompute ROS
    - Does NOT trigger agents
    - Does NOT modify graph

    Returns:
        ROSViewResponse with score breakdown and explanation

    Raises:
        404: No ROS results available (no query executed yet)
        500: Error reading cached results
    """
    try:
        # Prevent caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        cache = get_cache()

        # Check if cache has data
        if cache.is_empty():
            # Log at debug level since this is expected during polling
            logger.debug("ROS results requested but cache is empty (no query executed yet)")
            raise HTTPException(
                status_code=404,
                detail="No ROS results available. Execute a query via POST /api/query first."
            )

        # Get ROS result from cache
        ros_result = cache.get_last_ros_result()

        if ros_result is None:
            # Try to extract from last response
            last_response = cache.get_last_response()
            if last_response and 'ros_results' in last_response:
                ros_result = last_response['ros_results']
            else:
                raise HTTPException(
                    status_code=404,
                    detail="ROS computation not available for last query. The query may not have contained a drug-disease pair."
                )

        # Get drug/disease IDs
        drug_id, disease_id = cache.get_last_drug_disease_ids()

        # Extract drug/disease names from IDs or metadata
        # IDs are in format: canonical_id (hashed), so we extract from metadata if available
        metadata = ros_result.get('metadata', {})
        drug_name = metadata.get('drug_name', drug_id or 'Unknown Drug')
        disease_name = metadata.get('disease_name', disease_id or 'Unknown Disease')

        # Extract ROS score
        ros_score = ros_result.get('ros_score', 0.0)

        # Determine confidence level based on score
        if ros_score >= 7.0:
            confidence_level = "HIGH"
        elif ros_score >= 4.0:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"

        # Extract feature breakdown
        breakdown = ros_result.get('feature_breakdown', {})

        # Extract conflict penalty specifically
        conflict_penalty = breakdown.get('conflict_penalty', 0.0)

        # Extract explanation
        explanation = ros_result.get('explanation', 'No explanation available')

        # Build metadata for frontend
        frontend_metadata = {
            "computation_timestamp": metadata.get('computation_timestamp', datetime.utcnow().isoformat()),
            "num_supporting_evidence": metadata.get('num_supporting_evidence', 0),
            "num_contradicting_evidence": metadata.get('num_contradicting_evidence', 0),
            "num_suggesting_evidence": metadata.get('num_suggesting_evidence', 0),
            "distinct_agents": metadata.get('distinct_agents', [])
        }

        logger.info(f"✅ ROS view: score={ros_score:.2f}, confidence={confidence_level}")

        return ROSViewResponse(
            drug=drug_name,
            disease=disease_name,
            ros_score=ros_score,
            confidence_level=confidence_level,
            breakdown=breakdown,
            conflict_penalty=conflict_penalty,
            explanation=explanation,
            metadata=frontend_metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ROS results: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving ROS results: {str(e)}"
        )
