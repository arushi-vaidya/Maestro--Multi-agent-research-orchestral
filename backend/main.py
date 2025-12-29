"""
MAESTRO Backend - Main FastAPI Application
Feature 1: Basic Query Processing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
            "market": "active",
            "clinical": "pending",  # Not yet implemented
            "patent": "pending",    # Not yet implemented
            "trade": "pending"      # Not yet implemented
        }
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
        reload=True  # Auto-reload on code changes during development
    )