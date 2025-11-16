from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..agents.master_agent import MasterAgent

router = APIRouter()
master = MasterAgent()

class QueryRequest(BaseModel):
    query: str
    user_id: str = "demo_user"

@router.post("/analyze")
async def analyze_query(request: QueryRequest):
    try:
        result = await master.process_query(request.query)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/status")
async def get_agent_status():
    return {
        "agents": ["market", "clinical", "patent", "trade"],
        "status": "operational"
    }