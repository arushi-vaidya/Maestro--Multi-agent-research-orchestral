"""
MAESTRO API Routes
Feature 1: Basic query processing endpoint
STEP 7.6: API Façade Layer
"""
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import uuid

# Import our Master Agent
from agents.master_agent import MasterAgent

# STEP 7.6: Import API façade views
from api.views.cache import get_cache
from ros.scorer import calculate_ros, calculate_ros_with_gemini
from api.views import ros_view, graph_view, evidence_view, conflict_view, execution_view

# Import Chemical Composition Service
from services.chemical_composition_service import get_chemical_composition_service

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
    ros_method: Optional[str] = "deterministic"  # "deterministic" or "gemini_honest"
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Analyze GLP-1 agonist market opportunity in diabetes",
                "ros_method": "gemini_honest"  # NEW: Use Gemini for honest scoring
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

class ChemicalCompositionRequest(BaseModel):
    """Request for chemical composition analysis"""
    compound_name: str
    context: Optional[str] = None  # Additional context like indication or mechanism
    
    class Config:
        json_schema_extra = {
            "example": {
                "compound_name": "Semaglutide",
                "context": "GLP-1 receptor agonist for diabetes and weight loss"
            }
        }

class ChemicalCompositionResponse(BaseModel):
    """Chemical composition analysis response"""
    compound_name: str
    chemical_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    iupac_name: Optional[str] = None
    chemical_structure: Optional[str] = None
    structure_details: Optional[str] = None
    pharmacophore_elements: Optional[str] = None
    drug_similarity_analysis: Optional[str] = None
    similarity_score: Optional[float] = None
    similar_drugs: Optional[List[str]] = None
    mechanism_of_action: Optional[str] = None
    therapeutic_potential: Optional[str] = None
    structure_activity_relationship: Optional[str] = None
    key_interactions: Optional[str] = None
    safety_considerations: Optional[str] = None
    allergy_medical_cautions: Optional[str] = None
    suggested_alternatives: Optional[List[str]] = None
    optimization_potential: Optional[str] = None
    smiles: Optional[str] = None
    evidence_confidence: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    analysis_status: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "compound_name": "Semaglutide",
                "chemical_formula": "C187H291N45O59",
                "molecular_weight": 4113.6,
                "iupac_name": "...",
                "chemical_structure": "39-amino acid peptide derivative...",
                "mechanism_of_action": "GLP-1 receptor agonist...",
                "similarity_score": 0.85,
                "similar_drugs": ["Liraglutide", "Dulaglutide", "Tirzepatide"],
                "evidence_confidence": "HIGH"
            }
        }

class QueryResponse(BaseModel):
    # Existing fields (backward compatible)
    query_id: Optional[str] = None  # unique id for this query execution
    query: Optional[str] = None  # echo for UI display
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

@router.post("/chemical-composition", response_model=ChemicalCompositionResponse)
def analyze_chemical_composition(request: ChemicalCompositionRequest):
    """
    Analyze chemical composition of a compound using Gemini API
    
    This endpoint:
    1. Receives compound name and optional context
    2. Uses Gemini API to analyze chemical properties
    3. Returns detailed structure, formula, similarities, and therapeutic potential
    
    Returns:
    - Chemical formula and molecular weight
    - Detailed structure description
    - Comparison to similar approved drugs
    - Mechanism of action and therapeutic usefulness
    - Structure-activity relationships
    - Safety considerations
    """
    try:
        logger.info(f"Analyzing chemical composition for: {request.compound_name}")
        
        # Get chemical composition service
        service = get_chemical_composition_service()
        
        # Perform analysis
        analysis = service.analyze_chemical_composition(
            compound_name=request.compound_name,
            context=request.context
        )
        
        logger.info(f"✅ Chemical analysis completed for {request.compound_name}")
        
        # Convert to response model
        return ChemicalCompositionResponse(**analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing chemical composition: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing chemical composition: {str(e)}"
        )

@router.post("/query", response_model=QueryResponse)
def process_query(request: QueryRequest, response: Response):
    """
    Main query processing endpoint

    This endpoint:
    1. Receives a pharmaceutical query
    2. Routes it to the Master Agent
    3. Master Agent coordinates specialized agents
    4. Returns synthesized results
    5. STEP 7.6: Caches results for API façade views
    """
    try:
        # Prevent caching of query results
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        logger.info(f"Received query: {request.query[:100]}...")

        # Get Master Agent
        agent = get_master_agent()

        # Generate a unique query id for downstream retrieval
        query_id = str(uuid.uuid4())

        # Process query through Master Agent
        result = agent.process_query(request.query)

        logger.info(f"Query processed successfully. Insights: {len(result.get('insights', []))}")

        # Calculate ROS score from results using requested method
        ros_method = getattr(request, 'ros_method', 'deterministic')
        
        if ros_method == "gemini_honest":
            logger.info("[ROS] Using Gemini-based brutally honest scoring...")
            ros_result = calculate_ros_with_gemini(
                query=request.query,
                references=result.get('references', []),
                insights=result.get('insights', [])
            )
        else:
            logger.info("[ROS] Using deterministic scoring...")
            ros_result = calculate_ros(
                query=request.query,
                references=result.get('references', []),
                insights=result.get('insights', [])
            )
        
        logger.info(f"✅ ROS Score calculated: {ros_result['ros_score']:.2f} (method: {ros_result.get('calculation_method', 'unknown')})")

        # STEP 7.6: Cache results for API façade views
        cache = get_cache()
        cache.store_query_result(
            query_id=query_id,
            query=request.query,
            response=result,
            ros_result=ros_result,
            akgp_result=None,  # Can be populated if needed
            execution_metadata=result.get('execution_metadata'),
            drug_id=ros_result['metadata'].get('drug_name'),
            disease_id=ros_result['metadata'].get('disease_name')
        )
        logger.info("✅ Results cached for API façade views")

        # Include identifiers for frontend so it can request query-specific data
        result["query_id"] = query_id
        result["query"] = request.query
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
            "GET /api/agents/status": "Get agent status information",
            "GET /api/ros/latest": "Get ROS score for last query",
            "GET /api/graph/summary": "Get knowledge graph visualization data",
            "GET /api/evidence/timeline": "Get evidence timeline",
            "GET /api/conflicts/explanation": "Get conflict explanation",
            "GET /api/execution/status": "Get execution status"
        }
    }


# ==============================================================================
# STEP 7.6: INCLUDE API FAÇADE ROUTERS
# ==============================================================================

# Include all view routers
router.include_router(ros_view.router)
router.include_router(graph_view.router)
router.include_router(evidence_view.router)
router.include_router(conflict_view.router)
router.include_router(execution_view.router)