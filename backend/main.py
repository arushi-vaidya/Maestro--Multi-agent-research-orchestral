"""
MAESTRO Backend - Main FastAPI Application
Feature 1: Basic Query Processing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
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

# Custom filter to suppress expected 404s from polling endpoints
class SuppressPollingErrors(logging.Filter):
    def filter(self, record):
        # Suppress 404s for polling endpoints (expected during query execution)
        message = record.getMessage()
        if '404 Not Found' in message and ('/api/execution/status' in message or '/api/ros/latest' in message):
            return False
        return True

# Apply filter to uvicorn access logger
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.addFilter(SuppressPollingErrors())

# Lifespan event handler for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("="*60)
    logger.info("MAESTRO Backend Starting Up")
    logger.info("="*60)

    # Check for API keys
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
            logger.warning(f"  ⚠️  {key_name}: NOT SET")

    logger.info("\nDependency Check:")
    try:
        import fastapi
        logger.info(f"  ✅ FastAPI: {fastapi.__version__}")
    except ImportError:
        logger.error("  ❌ FastAPI: NOT INSTALLED")

    try:
        import uvicorn
        logger.info(f"  ✅ Uvicorn: {uvicorn.__version__}")
    except ImportError:
        logger.error("  ❌ Uvicorn: NOT INSTALLED")

    try:
        import requests
        logger.info(f"  ✅ Requests available")
    except ImportError:
        logger.warning("  ⚠️  Requests: NOT INSTALLED")

    logger.info("\nOptional Dependencies:")
    try:
        import chromadb
        logger.info(f"  ✅ ChromaDB: Available")
    except ImportError:
        logger.warning("  ⚠️  ChromaDB: NOT INSTALLED")

    try:
        import sentence_transformers
        logger.info(f"  ✅ Sentence Transformers: Available")
    except ImportError:
        logger.warning("  ⚠️  Sentence Transformers: NOT INSTALLED")

    logger.info("\nAgent Status:")
    try:
        from agents.master_agent import MasterAgent
        logger.info("  ✅ Master Agent: Available")
        logger.info("  ✅ Clinical Agent: Integrated")
        logger.info("  ✅ Patent Agent: Integrated")
        logger.info("  ✅ Market Agent: Integrated")
    except ImportError as e:
        logger.error(f"  ❌ Master Agent: Failed - {e}")

    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GOOGLE_API_KEY", "")
    serpapi_key = os.getenv("SERPAPI_KEY", "") or os.getenv("SERPAPI_API_KEY", "")
    
    logger.info("\n📋 Environment Check:")
    logger.info(f"   GROQ_API_KEY: {'✅ Set' if groq_key else '❌ Missing'}")
    logger.info(f"   GOOGLE_API_KEY: {'✅ Set' if gemini_key else '❌ Missing'}")
    logger.info(f"   SERPAPI_KEY: {'✅ Set' if serpapi_key else '⚠️  Missing (optional)'}")
    
    if not serpapi_key:
        logger.warning("⚠️  SERPAPI_KEY not set - Market Agent will use RAG only")
    
    try:
        from agents.master_agent import MasterAgent
        logger.info("🔧 Testing Master Agent initialization...")
        test_agent = MasterAgent()
        logger.info("✅ Master Agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Master Agent initialization FAILED: {e}")
    
    logger.info("="*60)
    logger.info("🚀 Backend ready at http://localhost:8000")
    logger.info("📊 Frontend should connect to: http://localhost:8000/api/query")
    logger.info("="*60)
    
    yield
    logger.info("Shutting down MAESTRO Backend...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="MAESTRO API",
    description="Multi-Agent Ensemble for Strategic Therapeutic Research Orchestration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
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
    """Detailed health check"""
    agent_status = {}
    try:
        from api.routes import get_master_agent
        agent = get_master_agent()
        agent_status = {
            "clinical": "active" if hasattr(agent, 'clinical_agent') and agent.clinical_agent else "unavailable",
            "patent": "active" if hasattr(agent, 'patent_agent') and agent.patent_agent else "unavailable",
            "market": "active" if hasattr(agent, 'market_agent') and agent.market_agent else "unavailable",
            "trade": "unavailable"
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

# Import and include API routes
from api.routes import router as api_router
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        access_log=True,
        log_level="info"
    )