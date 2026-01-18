"""
MAESTRO API Routes
Feature 1: Basic query processing endpoint
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

# Import our Master Agent
from agents.master_agent import MasterAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize Master Agent (singleton pattern)
master_agent = None

def get_master_agent():
    """Get or create Master Agent instance"""
    global master_agent
    if master_agent is None:
        master_agent = MasterAgent()
    return master_agent

# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Analyze GLP-1 agonist market opportunity in diabetes"
            }
        }

class Insight(BaseModel):
    agent: str
    finding: str
    confidence: int
    confidence_level: Optional[str] = None  # NEW: 'high', 'medium', 'low'
    total_trials: Optional[int] = None      # NEW: For clinical agent
    sources_used: Optional[Dict[str, int]] = None  # NEW: For market agent

class Reference(BaseModel):
    type: str  # 'patent', 'paper', 'clinical-trial', 'market-report'
    title: str
    source: str
    date: str
    url: str
    relevance: int
    agentId: str

class MarketIntelligence(BaseModel):
    """Market intelligence data structure from Market Agent"""
    agentId: str
    query: str
    sections: Dict[str, str]  # 7 sections: summary, market_overview, etc.
    confidence: Dict[str, Any]  # score, breakdown, explanation, level
    sources: Dict[str, List[str]]  # web URLs, internal doc IDs
    web_results: Optional[List[Dict[str, Any]]] = None  # Contains domain_tier (int), domain_weight (float)
    rag_results: Optional[List[Dict[str, Any]]] = None  # Contains metadata (dict), relevance_score (float)

class AgentExecutionStatus(BaseModel):
    """Agent execution status for real-time UI updates"""
    agent_id: str
    status: str  # 'running', 'completed', 'failed'
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result_count: Optional[int] = None  # trials for clinical, sources for market

class QueryResponse(BaseModel):
    # Existing fields (backward compatible)
    summary: str
    insights: List[Insight]
    recommendation: str
    timelineSaved: str
    references: List[Reference]

    # NEW FIELDS (additive, non-breaking)
    confidence_score: Optional[float] = None        # Aggregate confidence
    active_agents: Optional[List[str]] = None       # ['clinical', 'market']
    agent_execution_status: Optional[List[AgentExecutionStatus]] = None  # Detailed execution tracking
    market_intelligence: Optional[MarketIntelligence] = None  # Full market data
    total_trials: Optional[int] = None              # Clinical results count

@router.post("/query", response_model=QueryResponse)
def process_query(request: QueryRequest):
    """
    Main query processing endpoint
    
    This endpoint:
    1. Receives a pharmaceutical query
    2. Routes it to the Master Agent
    3. Master Agent coordinates specialized agents
    4. Returns synthesized results
    """
    try:
        logger.info(f"Received query: {request.query[:100]}...")
        
        # Get Master Agent
        agent = get_master_agent()
        
        # Process query through Master Agent
        result = agent.process_query(request.query)
        
        logger.info(f"Query processed successfully. Insights: {len(result.get('insights', []))}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@router.get("/agents/status")
async def get_agent_status():
    """Get status of all agents - reflects actual integration state"""
    try:
        agent = get_master_agent()

        # Determine actual agent availability based on master agent configuration
        status = {
            "master_agent": "active",
            "specialized_agents": {
                "clinical": "active" if hasattr(agent, 'clinical_agent') and agent.clinical_agent else "unavailable",
                "patent": "active" if hasattr(agent, 'patent_agent') and agent.patent_agent else "unavailable",
                "market": "active" if hasattr(agent, 'market_agent') and agent.market_agent else "unavailable",
                "trade": "unavailable"  # Not implemented
            }
        }

        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def api_root():
    """API information endpoint"""
    return {
        "message": "MAESTRO API - Feature 1: Basic Query Processing",
        "endpoints": {
            "POST /api/query": "Process pharmaceutical intelligence query",
            "GET /api/agents/status": "Get agent status information"
        }
    }