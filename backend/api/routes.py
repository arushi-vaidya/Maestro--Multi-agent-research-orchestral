"""
MAESTRO API Routes
Feature 1: Basic query processing endpoint
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
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

class Reference(BaseModel):
    type: str  # 'patent', 'paper', 'clinical-trial', 'market-report'
    title: str
    source: str
    date: str
    url: str
    relevance: int
    agentId: str

class QueryResponse(BaseModel):
    summary: str
    insights: List[Insight]
    recommendation: str
    timelineSaved: str
    references: List[Reference]

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
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
        result = await agent.process_query(request.query)
        
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
    """Get status of all agents"""
    try:
        agent = get_master_agent()
        return {
            "master_agent": "active",
            "specialized_agents": {
                "market": "active",
                "clinical": "pending",  # Not yet implemented in Feature 1
                "patent": "pending",
                "trade": "pending"
            }
        }
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