"""
Evidence View - Evidence Timeline Façade

Provides frontend-safe access to evidence timeline for chronological visualization.

CRITICAL CONSTRAINTS:
- READ-ONLY: Does NOT modify graph
- Does NOT trigger agents
- Does NOT recompute temporal weights
- ONLY queries existing evidence from AKGP

Endpoints:
- GET /api/evidence/timeline: Get chronologically sorted evidence
"""

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import random

from akgp.schema import NodeType, SourceType, EvidenceQuality
from api.views.cache import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evidence", tags=["Evidence"])


# ==============================================================================
# RESPONSE MODELS
# ==============================================================================

class EvidenceTimelineEvent(BaseModel):
    """
    Evidence timeline event for chronological visualization

    Represents a single piece of evidence on a timeline.
    """
    timestamp: datetime  # extraction_timestamp or validity_start
    source: str  # Agent name or API source
    polarity: Literal["SUPPORTS", "SUGGESTS", "CONTRADICTS"]
    confidence: float  # 0.0-1.0
    quality: Literal["LOW", "MEDIUM", "HIGH"]
    reference_id: str  # NCT ID, patent number, URL, etc.
    summary: str  # Brief evidence summary
    agent_id: str  # clinical, patent, market, literature
    recency_weight: Optional[float] = None  # Temporal decay weight

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-03-15T10:30:00Z",
                "source": "ClinicalTrials.gov",
                "polarity": "SUPPORTS",
                "confidence": 0.85,
                "quality": "HIGH",
                "reference_id": "NCT05123456",
                "summary": "Phase 3 trial showing 12% reduction in HbA1c",
                "agent_id": "clinical",
                "recency_weight": 0.92
            }
        }


class EvidenceTimelineResponse(BaseModel):
    """
    Complete evidence timeline response

    Contains chronologically sorted evidence events.
    """
    events: List[EvidenceTimelineEvent]
    total_count: int
    date_range: Dict[str, Optional[str]]  # earliest, latest
    agent_distribution: Dict[str, int]  # Count by agent
    polarity_distribution: Dict[str, int]  # Count by polarity

    class Config:
        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "timestamp": "2024-01-15T00:00:00Z",
                        "source": "ClinicalTrials.gov",
                        "polarity": "SUPPORTS",
                        "confidence": 0.9,
                        "quality": "HIGH",
                        "reference_id": "NCT05123456",
                        "summary": "Phase 3 trial success",
                        "agent_id": "clinical",
                        "recency_weight": 0.95
                    }
                ],
                "total_count": 1,
                "date_range": {"earliest": "2024-01-15T00:00:00Z", "latest": "2024-01-15T00:00:00Z"},
                "agent_distribution": {"clinical": 1},
                "polarity_distribution": {"SUPPORTS": 1}
            }
        }


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _normalize_quality(quality: str) -> str:
    """Normalize quality to uppercase"""
    if isinstance(quality, str):
        return quality.upper()
    return "MEDIUM"  # Default


def _infer_polarity_from_relationships(evidence_id: str, graph_manager) -> str:
    """
    Infer polarity from relationships

    Check what type of relationships this evidence supports.
    """
    try:
        # Get relationships where this evidence is referenced
        # This is a simplification - in production, would query by evidence_id
        return "SUGGESTS"  # Default polarity if can't determine
    except Exception:
        return "SUGGESTS"


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.get("/timeline", response_model=EvidenceTimelineResponse)
def get_evidence_timeline(
    response: Response,
    limit: int = Query(100, description="Maximum events to return", ge=1, le=500),
    agent_filter: Optional[str] = Query(None, description="Filter by agent (clinical, patent, market, literature)"),
    quality_filter: Optional[str] = Query(None, description="Filter by quality (LOW, MEDIUM, HIGH)")
):
    """
    Get evidence timeline for chronological visualization

    This endpoint:
    - Reads evidence from AKGP graph (READ-ONLY)
    - Sorts by extraction timestamp (chronological order)
    - Does NOT recompute temporal weights
    - Does NOT trigger agents

    Query Parameters:
        limit: Maximum number of events to return (default: 100, max: 500)
        agent_filter: Filter by specific agent (e.g., 'clinical')
        quality_filter: Filter by evidence quality (e.g., 'HIGH')

    Returns:
        EvidenceTimelineResponse with chronologically sorted events

    Raises:
        500: Error reading evidence
    """
    try:
        # Prevent caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Import here to avoid circular dependencies
        from api.routes import get_master_agent

        # Get graph manager from master agent
        master = get_master_agent()
        graph_manager = master.graph_manager

        events = []
        agent_dist = {}
        polarity_dist = {}
        
        # Strategy 1: Try to get evidence from current query context (Cache)
        cache = get_cache()
        last_response = cache.get_last_response()
        
        if last_response and last_response.get('references'):
            logger.info(f"🎯 Using {len(last_response['references'])} references from current query cache")
            
            for ref in last_response['references']:
                try:
                    # Apply filters
                    agent_id = ref.get('agentId', 'unknown')
                    if agent_filter and agent_id != agent_filter:
                        continue
                        
                    # Map Reference to EvidenceTimelineEvent
                    # References usually have: type, title, source, date, url, relevance, agentId, summary
                    
                    # Parse timestamp (handle various formats)
                    date_str = ref.get('date', '')
                    timestamp = datetime.utcnow()
                    if date_str:
                        # Try simplistic parsing or just use current time if year-only
                        if len(date_str) == 4 and date_str.isdigit():
                            # It's a year
                            timestamp = datetime(int(date_str), 1, 1)
                        else:
                            # Assume current for visualization if parsing fails, or try basic parsing
                            try:
                                timestamp = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            except:
                                pass
                    
                    # Determine polarity/confidence/quality from relevance
                    confidence = float(ref.get('relevance', 80)) / 100.0
                    quality = "HIGH" if confidence > 0.8 else ("MEDIUM" if confidence > 0.5 else "LOW")
                    
                    if quality_filter and quality != quality_filter:
                        continue
                        
                    event = EvidenceTimelineEvent(
                        timestamp=timestamp,
                        source=ref.get('source', 'Unknown'),
                        polarity="SUPPORTS", # Default for now as most refs support the query
                        confidence=confidence,
                        quality=quality,
                        reference_id=ref.get('url') or ref.get('nct_id') or ref.get('patent_number') or ref.get('pmid') or 'unknown',
                        summary=ref.get('summary', ref.get('title', ''))[:200],
                        agent_id=agent_id,
                        recency_weight=None
                    )
                    
                    events.append(event)
                    agent_dist[agent_id] = agent_dist.get(agent_id, 0) + 1
                    polarity_dist["SUPPORTS"] = polarity_dist.get("SUPPORTS", 0) + 1
                    
                except Exception as e:
                    logger.warning(f"Error mapping cached reference: {e}")
                    continue
                    
        # Strategy 2: Fallback to global graph query if no cached events found
        if not events:
            logger.info("🌍 No cached references found - falling back to global graph query")
            
            # Fetch all evidence nodes
            evidence_nodes = graph_manager.find_nodes_by_type(NodeType.EVIDENCE, limit=limit * 2)  # Fetch extra for filtering
            logger.info(f"Found {len(evidence_nodes)} evidence nodes")

            event_count = 0  # Track actual event count for deterministic spread

            for node in evidence_nodes:
                try:
                    # Apply filters
                    if agent_filter and node.get('agent_id') != agent_filter:
                        continue

                    if quality_filter and node.get('quality', '').upper() != quality_filter.upper():
                        continue

                    # Extract timestamp
                    timestamp_str = node.get('extraction_timestamp') or node.get('validity_start') or node.get('created_at')
                    if timestamp_str:
                        if isinstance(timestamp_str, str):
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        elif isinstance(timestamp_str, datetime):
                            timestamp = timestamp_str
                        else:
                            # Generate synthetic timestamp for demo - spread across past year
                            days_ago = (event_count * 4) % 365  # Spread every 4 days
                            timestamp = datetime.utcnow() - timedelta(days=days_ago)
                    else:
                        # Generate synthetic timestamp for demo (spread across past year)
                        days_ago = (event_count * 4) % 365  # Spread every 4 days
                        timestamp = datetime.utcnow() - timedelta(days=days_ago)

                    # Increment after using for timestamp
                    event_count += 1

                    # Extract polarity (from metadata or infer)
                    # Note: Polarity is typically stored in relationships, not evidence nodes directly
                    # For façade, we'll use a simplified approach
                    polarity = node.get('polarity', 'SUGGESTS')  # Default to SUGGESTS if not specified

                    # Extract fields
                    source = node.get('api_source') or node.get('agent_name', 'Unknown')
                    confidence = node.get('confidence_score', 0.5)
                    quality = _normalize_quality(node.get('quality', 'MEDIUM'))
                    reference_id = node.get('raw_reference', node.get('id', 'Unknown'))
                    summary = node.get('summary', '')[:200]  # Truncate for timeline
                    agent_id = node.get('agent_id', 'unknown')

                    # Create event
                    event = EvidenceTimelineEvent(
                        timestamp=timestamp,
                        source=source,
                        polarity=polarity,
                        confidence=confidence,
                        quality=quality,
                        reference_id=reference_id,
                        summary=summary,
                        agent_id=agent_id,
                        recency_weight=None  # Frontend can calculate if needed
                    )
                    events.append(event)

                    # Update distributions
                    agent_dist[agent_id] = agent_dist.get(agent_id, 0) + 1
                    polarity_dist[polarity] = polarity_dist.get(polarity, 0) + 1

                    # Stop if we've collected enough
                    if len(events) >= limit:
                        break

                except Exception as e:
                    logger.warning(f"Error processing evidence node {node.get('id')}: {e}")
                    continue

        # Sort by timestamp (descending - most recent first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        # Calculate date range
        if events:
            earliest = min(e.timestamp for e in events).isoformat()
            latest = max(e.timestamp for e in events).isoformat()
        else:
            earliest = None
            latest = None

        logger.info(f"✅ Evidence timeline: {len(events)} events, {len(agent_dist)} agents")

        return EvidenceTimelineResponse(
            events=events,
            total_count=len(events),
            date_range={"earliest": earliest, "latest": latest},
            agent_distribution=agent_dist,
            polarity_distribution=polarity_dist
        )

    except Exception as e:
        logger.error(f"Error retrieving evidence timeline: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving evidence timeline: {str(e)}"
        )
