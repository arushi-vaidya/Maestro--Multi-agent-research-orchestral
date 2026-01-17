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
    """Detailed health check"""
    return {
        "status": "healthy",
        "agents": {
            "market": "pending",
            "clinical": "active",  # Not yet implemented
            "patent": "pending",    # Not yet implemented
            "trade": "pending"      # Not yet implemented
        }
    }

# Import and include API routes
from api.routes import router as api_router
app.include_router(api_router, prefix="/api")

# ADDED: Startup diagnostics
@app.on_event("startup")
async def startup_diagnostics():
    """
    Run diagnostic checks on startup to catch configuration issues early
    """
    logger.info("="*60)
    logger.info("🎼 MAESTRO Backend Starting...")
    logger.info("="*60)
    
    # Check critical API keys
    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GOOGLE_API_KEY", "")
    serpapi_key = os.getenv("SERPAPI_KEY", "") or os.getenv("SERPAPI_API_KEY", "")
    
    logger.info("📋 Environment Check:")
    logger.info(f"   GROQ_API_KEY: {'✅ Set' if groq_key else '❌ Missing'}")
    logger.info(f"   GOOGLE_API_KEY: {'✅ Set' if gemini_key else '❌ Missing'}")
    logger.info(f"   SERPAPI_KEY: {'✅ Set' if serpapi_key else '⚠️  Missing (optional)'}")
    
    if not groq_key and not gemini_key:
        logger.error("❌ CRITICAL: No LLM API keys configured!")
        logger.error("   Set GROQ_API_KEY or GOOGLE_API_KEY in .env file")
        logger.error("   Backend will fail on first query")
    
    if not serpapi_key:
        logger.warning("⚠️  SERPAPI_KEY not set - Market Agent will use RAG only")
        logger.warning("   Get free key: https://serpapi.com/users/sign_up")
    
    # Test agent initialization
    try:
        from agents.master_agent import MasterAgent
        logger.info("🔧 Testing Master Agent initialization...")
        test_agent = MasterAgent()
        logger.info("✅ Master Agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Master Agent initialization FAILED: {e}")
        logger.error("   Backend may be unstable")
    
    logger.info("="*60)
    logger.info("🚀 Backend ready at http://localhost:8000")
    logger.info("📊 Frontend should connect to: http://localhost:8000/api/query")
    logger.info("="*60)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Auto-reload on code changes during development
    )