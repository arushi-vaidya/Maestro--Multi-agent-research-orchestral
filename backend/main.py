"""
MAESTRO Backend - Main FastAPI Application
Feature 1: Basic Query Processing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MAESTRO API",
    description="Multi-Agent Ensemble for Strategic Therapeutic Research Orchestration",
    version="1.0.0"
)

# CORS configuration - Allow your frontend to connect
# CORS configuration - Allow your frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Localhost origins (for when frontend runs on localhost)
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
        # IP address origins (for network access)
        "http://172.20.10.2:3000",
        "http://172.20.10.2:5173",
        "http://172.20.10.2:5174",
        "http://172.20.10.2:8080",
        "http://172.20.10.2:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "MAESTRO API",
        "version": "1.0.0",
        "feature": "Feature 1 - Basic Query Processing"
    }

@app.get("/health")
async def health_check():
    """Detailed health check - consistent with actual agent availability"""
    # Check actual agent status dynamically
    agent_status = {}
    try:
        from api.routes import get_master_agent
        agent = get_master_agent()
        agent_status = {
            "clinical": "active" if hasattr(agent, 'clinical_agent') and agent.clinical_agent else "unavailable",
            "patent": "active" if hasattr(agent, 'patent_agent') and agent.patent_agent else "unavailable",
            "market": "active" if hasattr(agent, 'market_agent') and agent.market_agent else "unavailable",
            "trade": "unavailable"  # Not implemented
        }
    except Exception as e:
        logger.warning(f"Could not determine agent status: {e}")
        agent_status = {
            "clinical": "unknown",
            "patent": "unknown",
            "market": "unknown",
            "trade": "unavailable"
        }

    return {
        "status": "healthy",
        "agents": agent_status
    }

@app.on_event("startup")
async def startup_checks():
    """Perform startup dependency and configuration checks"""
    logger.info("="*60)
    logger.info("MAESTRO Backend Starting Up")
    logger.info("="*60)

    # Check for API keys (warn if missing, don't crash)
    api_keys = {
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "SERPAPI_API_KEY": os.getenv("SERPAPI_API_KEY")
    }

    logger.info("API Key Configuration:")
    for key_name, key_value in api_keys.items():
        if key_value:
            logger.info(f"  ✅ {key_name}: SET")
        else:
            logger.warning(f"  ⚠️  {key_name}: NOT SET - Some features may be limited")

    # Check critical dependencies
    logger.info("\nDependency Check:")
    dependencies_status = []

    try:
        import fastapi
        logger.info(f"  ✅ FastAPI: {fastapi.__version__}")
        dependencies_status.append(("FastAPI", True))
    except ImportError:
        logger.error("  ❌ FastAPI: NOT INSTALLED")
        dependencies_status.append(("FastAPI", False))

    try:
        import uvicorn
        logger.info(f"  ✅ Uvicorn: {uvicorn.__version__}")
        dependencies_status.append(("Uvicorn", True))
    except ImportError:
        logger.error("  ❌ Uvicorn: NOT INSTALLED")
        dependencies_status.append(("Uvicorn", False))

    try:
        import requests
        logger.info(f"  ✅ Requests: {requests.__version__}")
        dependencies_status.append(("Requests", True))
    except ImportError:
        logger.warning("  ⚠️  Requests: NOT INSTALLED - API calls will fail")
        dependencies_status.append(("Requests", False))

    # Optional dependencies
    logger.info("\nOptional Dependencies:")

    try:
        import chromadb
        logger.info(f"  ✅ ChromaDB: Available (RAG enabled)")
    except ImportError:
        logger.warning("  ⚠️  ChromaDB: NOT INSTALLED - RAG features disabled")

    try:
        import sentence_transformers
        logger.info(f"  ✅ Sentence Transformers: Available")
    except ImportError:
        logger.warning("  ⚠️  Sentence Transformers: NOT INSTALLED - Embeddings disabled")

    # Agent initialization status
    logger.info("\nAgent Status:")
    try:
        from agents.master_agent import MasterAgent
        logger.info("  ✅ Master Agent: Available")
        logger.info("  ✅ Clinical Agent: Integrated")
        logger.info("  ✅ Patent Agent: Integrated")
        logger.info("  ✅ Market Agent: Integrated")
        logger.info("  ⚠️  Trade Agent: Not Implemented")
    except ImportError as e:
        logger.error(f"  ❌ Master Agent: Failed to import - {e}")

    logger.info("\n" + "="*60)
    logger.info("MAESTRO Backend Ready")
    logger.info("API Endpoints: http://localhost:8000/docs")
    logger.info("="*60 + "\n")

# Import and include API routes
from api.routes import router as api_router
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Auto-reload on code changes during development
    )