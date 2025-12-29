#!/bin/bash

# MAESTRO Backend Structure Setup Script
# This script creates a comprehensive, production-ready backend structure
# for the MAESTRO multi-agent pharmaceutical intelligence system

set -e  # Exit on error

echo "🎼 Setting up MAESTRO Backend Structure..."
echo "================================================"

# Base backend directory
BACKEND_DIR="backend"

# Create main directories
echo "📁 Creating main directory structure..."

# 1. Agents directory (with missing agents)
mkdir -p ${BACKEND_DIR}/agents/base
mkdir -p ${BACKEND_DIR}/agents/specialized

# 2. API layer
mkdir -p ${BACKEND_DIR}/api/endpoints
mkdir -p ${BACKEND_DIR}/api/middleware
mkdir -p ${BACKEND_DIR}/api/schemas

# 3. Data Sources
mkdir -p ${BACKEND_DIR}/data_sources/iqvia
mkdir -p ${BACKEND_DIR}/data_sources/patents
mkdir -p ${BACKEND_DIR}/data_sources/clinical_trials
mkdir -p ${BACKEND_DIR}/data_sources/trade
mkdir -p ${BACKEND_DIR}/data_sources/web

# 4. Processing
mkdir -p ${BACKEND_DIR}/processing/harmonization
mkdir -p ${BACKEND_DIR}/processing/fusion
mkdir -p ${BACKEND_DIR}/processing/validation

# 5. Utils
mkdir -p ${BACKEND_DIR}/utils/reporting
mkdir -p ${BACKEND_DIR}/utils/logging
mkdir -p ${BACKEND_DIR}/utils/cache

# 6. Configuration
mkdir -p ${BACKEND_DIR}/config/agents
mkdir -p ${BACKEND_DIR}/config/databases
mkdir -p ${BACKEND_DIR}/config/llm

# 7. LangChain/LangGraph specific
mkdir -p ${BACKEND_DIR}/langchain_config
mkdir -p ${BACKEND_DIR}/langchain_config/chains
mkdir -p ${BACKEND_DIR}/langchain_config/graphs
mkdir -p ${BACKEND_DIR}/langchain_config/prompts
mkdir -p ${BACKEND_DIR}/langchain_config/tools

# 8. Vector Store for RAG
mkdir -p ${BACKEND_DIR}/vector_store/embeddings
mkdir -p ${BACKEND_DIR}/vector_store/indices
mkdir -p ${BACKEND_DIR}/vector_store/documents

# 9. Database models
mkdir -p ${BACKEND_DIR}/models/schemas
mkdir -p ${BACKEND_DIR}/models/repositories

# 10. Services layer
mkdir -p ${BACKEND_DIR}/services/orchestration
mkdir -p ${BACKEND_DIR}/services/query_processing
mkdir -p ${BACKEND_DIR}/services/report_generation

# 11. Tests
mkdir -p ${BACKEND_DIR}/tests/unit/agents
mkdir -p ${BACKEND_DIR}/tests/unit/services
mkdir -p ${BACKEND_DIR}/tests/integration
mkdir -p ${BACKEND_DIR}/tests/fixtures

# 12. Background tasks
mkdir -p ${BACKEND_DIR}/tasks/celery
mkdir -p ${BACKEND_DIR}/tasks/workers

# 13. Cache and storage
mkdir -p ${BACKEND_DIR}/storage/temp
mkdir -p ${BACKEND_DIR}/storage/reports
mkdir -p ${BACKEND_DIR}/storage/logs

echo "📝 Creating agent files..."

# Create base agent class
cat > ${BACKEND_DIR}/agents/base/__init__.py << 'EOF'
"""Base agent classes for MAESTRO system."""
EOF

cat > ${BACKEND_DIR}/agents/base/agent_base.py << 'EOF'
"""
Base Agent Class for MAESTRO
All specialized agents inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor
from langchain.schema import BaseMessage
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all MAESTRO agents."""
    
    def __init__(self, name: str, description: str, llm=None):
        self.name = name
        self.description = description
        self.llm = llm
        self.executor: Optional[AgentExecutor] = None
        
    @abstractmethod
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a query and return results."""
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """Return list of tools available to this agent."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
    
    async def validate_input(self, query: str) -> bool:
        """Validate input query."""
        return bool(query and len(query.strip()) > 0)
    
    async def log_interaction(self, query: str, response: Dict[str, Any]):
        """Log agent interactions for debugging and monitoring."""
        logger.info(f"Agent: {self.name} | Query: {query[:100]}...")
        logger.debug(f"Response: {response}")
EOF

# Create missing agents - Internal Knowledge Agent
cat > ${BACKEND_DIR}/agents/specialized/__init__.py << 'EOF'
"""Specialized agents for MAESTRO system."""
EOF

cat > ${BACKEND_DIR}/agents/specialized/internal_agent.py << 'EOF'
"""
Internal Knowledge Agent
Handles RAG-based retrieval from internal documents
"""
from typing import Dict, Any, List
from agents.base.agent_base import BaseAgent
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

class InternalKnowledgeAgent(BaseAgent):
    """
    Agent for querying internal company documents using RAG.
    Uses vector store to retrieve relevant internal knowledge.
    """
    
    def __init__(self, vector_store_path: str, llm=None):
        super().__init__(
            name="InternalKnowledgeAgent",
            description="Retrieves and summarizes internal documents, strategies, and institutional knowledge",
            llm=llm
        )
        self.vector_store_path = vector_store_path
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self._initialize_vector_store()
        
    def _initialize_vector_store(self):
        """Initialize vector store for RAG."""
        # TODO: Implement vector store initialization
        pass
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process internal knowledge queries using RAG.
        
        Args:
            query: User query about internal documents
            context: Additional context for the query
            
        Returns:
            Dict containing retrieved documents and synthesized answer
        """
        if not await self.validate_input(query):
            return {"error": "Invalid query"}
        
        # TODO: Implement RAG query processing
        result = {
            "agent": self.name,
            "query": query,
            "documents": [],
            "answer": "",
            "sources": []
        }
        
        await self.log_interaction(query, result)
        return result
    
    def get_tools(self) -> List:
        """Return tools for internal document search."""
        return []
    
    def get_system_prompt(self) -> str:
        """Return system prompt for internal knowledge agent."""
        return """You are an internal knowledge specialist for a pharmaceutical company.
        Your role is to retrieve and summarize information from internal documents,
        strategy decks, meeting minutes, and field reports. Always cite your sources."""
EOF

# Create Web Intelligence Agent
cat > ${BACKEND_DIR}/agents/specialized/web_agent.py << 'EOF'
"""
Web Intelligence Agent
Handles real-time web searches, PubMed queries, and regulatory updates
"""
from typing import Dict, Any, List
from agents.base.agent_base import BaseAgent
from langchain.tools import DuckDuckGoSearchRun
from langchain.utilities import GoogleSerperAPIWrapper

class WebIntelligenceAgent(BaseAgent):
    """
    Agent for real-time web intelligence gathering.
    Searches web, PubMed, FDA/EMA announcements, and pharma news.
    """
    
    def __init__(self, llm=None):
        super().__init__(
            name="WebIntelligenceAgent",
            description="Real-time web search and pharmaceutical intelligence gathering",
            llm=llm
        )
        self.search_tool = None
        self._initialize_tools()
        
    def _initialize_tools(self):
        """Initialize web search tools."""
        # TODO: Initialize search tools
        pass
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process web intelligence queries.
        
        Args:
            query: User query for web search
            context: Additional context including search domains
            
        Returns:
            Dict containing search results and analysis
        """
        if not await self.validate_input(query):
            return {"error": "Invalid query"}
        
        # TODO: Implement web search and analysis
        result = {
            "agent": self.name,
            "query": query,
            "search_results": [],
            "pubmed_results": [],
            "regulatory_updates": [],
            "news": [],
            "summary": ""
        }
        
        await self.log_interaction(query, result)
        return result
    
    def get_tools(self) -> List:
        """Return web search tools."""
        return []
    
    def get_system_prompt(self) -> str:
        """Return system prompt for web intelligence agent."""
        return """You are a pharmaceutical web intelligence specialist.
        Your role is to search and analyze real-time web information,
        scientific literature, regulatory announcements, and industry news.
        Always verify information from multiple sources."""
EOF

# Create enhanced Master Agent
cat > ${BACKEND_DIR}/agents/master_agent_enhanced.py << 'EOF'
"""
Enhanced Master Agent with LangGraph Integration
Orchestrates all specialized agents using LangGraph state machine
"""
from typing import Dict, Any, List, Annotated, TypedDict
from langchain.schema import BaseMessage
from langgraph.graph import StateGraph, END
from agents.base.agent_base import BaseAgent
import operator

class MaestroState(TypedDict):
    """State for MAESTRO orchestration graph."""
    query: str
    intent: Dict[str, Any]
    agents_to_call: List[str]
    agent_results: Annotated[Dict[str, Any], operator.add]
    synthesized_result: Dict[str, Any]
    final_report: str
    errors: List[str]

class EnhancedMasterAgent(BaseAgent):
    """
    Master Agent that orchestrates all specialized agents using LangGraph.
    Implements intent classification, task decomposition, and result synthesis.
    """
    
    def __init__(self, llm=None):
        super().__init__(
            name="MasterAgent",
            description="Orchestrates all specialized agents for complex pharmaceutical queries",
            llm=llm
        )
        self.workflow = None
        self._initialize_workflow()
    
    def _initialize_workflow(self):
        """Initialize LangGraph workflow for agent orchestration."""
        workflow = StateGraph(MaestroState)
        
        # Add nodes for each step
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("decompose_tasks", self._decompose_tasks)
        workflow.add_node("coordinate_agents", self._coordinate_agents)
        workflow.add_node("synthesize_results", self._synthesize_results)
        workflow.add_node("generate_report", self._generate_report)
        
        # Define edges
        workflow.set_entry_point("classify_intent")
        workflow.add_edge("classify_intent", "decompose_tasks")
        workflow.add_edge("decompose_tasks", "coordinate_agents")
        workflow.add_edge("coordinate_agents", "synthesize_results")
        workflow.add_edge("synthesize_results", "generate_report")
        workflow.add_edge("generate_report", END)
        
        self.workflow = workflow.compile()
    
    async def _classify_intent(self, state: MaestroState) -> MaestroState:
        """Classify user intent using LLM."""
        # TODO: Implement intent classification
        state["intent"] = {"type": "multi_source", "complexity": "high"}
        return state
    
    async def _decompose_tasks(self, state: MaestroState) -> MaestroState:
        """Decompose complex query into agent-specific tasks."""
        # TODO: Implement task decomposition
        state["agents_to_call"] = ["market", "patent", "clinical", "trade"]
        return state
    
    async def _coordinate_agents(self, state: MaestroState) -> MaestroState:
        """Coordinate specialized agents in parallel or sequential mode."""
        # TODO: Implement agent coordination
        state["agent_results"] = {}
        return state
    
    async def _synthesize_results(self, state: MaestroState) -> MaestroState:
        """Synthesize results from multiple agents."""
        # TODO: Implement result synthesis
        state["synthesized_result"] = {}
        return state
    
    async def _generate_report(self, state: MaestroState) -> MaestroState:
        """Generate final report."""
        # TODO: Implement report generation
        state["final_report"] = ""
        return state
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process query through the orchestration workflow."""
        initial_state: MaestroState = {
            "query": query,
            "intent": {},
            "agents_to_call": [],
            "agent_results": {},
            "synthesized_result": {},
            "final_report": "",
            "errors": []
        }
        
        result = await self.workflow.ainvoke(initial_state)
        return result
    
    def get_tools(self) -> List:
        """Master agent doesn't use tools directly."""
        return []
    
    def get_system_prompt(self) -> str:
        """Return system prompt for master agent."""
        return """You are the Master Agent of MAESTRO, a pharmaceutical intelligence system.
        Your role is to understand complex queries, coordinate specialized agents,
        and synthesize comprehensive responses."""
EOF

echo "⚙️ Creating configuration files..."

# LangChain configuration
cat > ${BACKEND_DIR}/config/llm/llm_config.py << 'EOF'
"""LLM Configuration for MAESTRO."""
from typing import Dict, Any
import os
from pydantic import BaseSettings

class LLMConfig(BaseSettings):
    """Configuration for LLM providers."""
    
    # OpenAI/Gemini settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Model settings
    DEFAULT_MODEL: str = "gemini-pro"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 4000
    
    # LangChain settings
    LANGCHAIN_TRACING: bool = True
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    
    class Config:
        env_file = ".env"

llm_config = LLMConfig()
EOF

# Agent configuration
cat > ${BACKEND_DIR}/config/agents/agent_config.yaml << 'EOF'
# MAESTRO Agent Configuration

agents:
  master:
    enabled: true
    model: "gemini-pro"
    max_retries: 3
    timeout: 300
    
  market:
    enabled: true
    model: "gemini-pro"
    data_source: "iqvia"
    cache_ttl: 3600
    
  patent:
    enabled: true
    model: "gemini-pro"
    data_sources:
      - "uspto"
      - "epo"
    cache_ttl: 7200
    
  clinical:
    enabled: true
    model: "gemini-pro"
    data_sources:
      - "clinicaltrials_gov"
      - "who_ictrp"
    cache_ttl: 3600
    
  trade:
    enabled: true
    model: "gemini-pro"
    data_sources:
      - "data_gov_in"
      - "un_comtrade"
    cache_ttl: 7200
    
  internal_knowledge:
    enabled: true
    model: "gemini-pro"
    vector_store: "chroma"
    embedding_model: "text-embedding-ada-002"
    chunk_size: 1000
    chunk_overlap: 200
    
  web_intelligence:
    enabled: true
    model: "gemini-pro"
    search_providers:
      - "google_serper"
      - "duckduckgo"
    pubmed_enabled: true
    max_search_results: 10
EOF

# Database configuration
cat > ${BACKEND_DIR}/config/databases/database_config.py << 'EOF'
"""Database configuration for MAESTRO."""
import os
from pydantic import BaseSettings

class DatabaseConfig(BaseSettings):
    """Configuration for databases."""
    
    # PostgreSQL for structured data
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "maestro")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "maestro")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    
    # Redis for caching
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # Vector DB for RAG
    VECTOR_DB_TYPE: str = "chroma"  # Options: chroma, pinecone, weaviate
    VECTOR_DB_PATH: str = "./vector_store/indices"
    
    class Config:
        env_file = ".env"

database_config = DatabaseConfig()
EOF

echo "🔧 Creating utility files..."

# Enhanced logger
cat > ${BACKEND_DIR}/utils/logging/logger.py << 'EOF'
"""Enhanced logging configuration for MAESTRO."""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class MaestroLogger:
    """Custom logger for MAESTRO system."""
    
    def __init__(self, name: str, log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level))
        
        # Create handlers
        self._add_console_handler()
        self._add_file_handler()
        
    def _add_console_handler(self):
        """Add console handler with formatting."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def _add_file_handler(self):
        """Add rotating file handler."""
        log_dir = Path("storage/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_dir / "maestro.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def log_agent_interaction(self, agent_name: str, query: str, response: dict):
        """Log agent interactions in structured format."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "query": query,
            "response_summary": str(response)[:200],
            "success": "error" not in response
        }
        self.logger.info(json.dumps(log_entry))

def get_logger(name: str) -> MaestroLogger:
    """Factory function to get logger instance."""
    return MaestroLogger(name)
EOF

# Cache manager
cat > ${BACKEND_DIR}/utils/cache/cache_manager.py << 'EOF'
"""Cache management for MAESTRO."""
import redis
import json
from typing import Any, Optional
import hashlib

class CacheManager:
    """Manages caching for agent responses."""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
    
    def _generate_key(self, agent_name: str, query: str) -> str:
        """Generate cache key from agent and query."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        return f"maestro:{agent_name}:{query_hash}"
    
    def get(self, agent_name: str, query: str) -> Optional[dict]:
        """Get cached response."""
        key = self._generate_key(agent_name, query)
        cached = self.redis_client.get(key)
        return json.loads(cached) if cached else None
    
    def set(self, agent_name: str, query: str, response: dict, ttl: int = 3600):
        """Cache response with TTL."""
        key = self._generate_key(agent_name, query)
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(response)
        )
    
    def invalidate(self, agent_name: str, query: str):
        """Invalidate cached response."""
        key = self._generate_key(agent_name, query)
        self.redis_client.delete(key)
EOF

echo "🧪 Creating test structure..."

# Test configuration
cat > ${BACKEND_DIR}/tests/__init__.py << 'EOF'
"""Test suite for MAESTRO."""
EOF

cat > ${BACKEND_DIR}/tests/conftest.py << 'EOF'
"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    return Mock()

@pytest.fixture
def sample_query():
    """Sample pharmaceutical query."""
    return "What's the market size for diabetes drugs in India?"

@pytest.fixture
def mock_agent_response():
    """Mock agent response."""
    return {
        "agent": "TestAgent",
        "query": "test query",
        "results": [],
        "confidence": 0.95
    }
EOF

echo "📦 Creating requirements additions..."

cat > ${BACKEND_DIR}/requirements_additions.txt << 'EOF'
# Additional requirements for enhanced MAESTRO backend

# LangChain & LangGraph
langchain>=0.1.0
langgraph>=0.0.20
langchain-community>=0.0.20
langchain-google-genai>=0.0.5

# Vector Stores & Embeddings
chromadb>=0.4.0
faiss-cpu>=1.7.4
sentence-transformers>=2.2.2

# Database & Caching
redis>=5.0.0
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0

# Async & Task Queue
celery>=5.3.0
aioredis>=2.0.0
asyncio>=3.4.3

# Data Processing
pandas>=2.0.0
numpy>=1.24.0
pydantic>=2.0.0
pyyaml>=6.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0

# API & Web
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6

# Monitoring & Logging
prometheus-client>=0.19.0
structlog>=23.2.0

# Utilities
python-dotenv>=1.0.0
tenacity>=8.2.0  # For retry logic
EOF

echo "📄 Creating __init__.py files..."

# Create all __init__.py files
find ${BACKEND_DIR} -type d -exec touch {}/__init__.py \;

echo "✅ Creating README for backend structure..."

cat > ${BACKEND_DIR}/README_STRUCTURE.md << 'EOF'
# MAESTRO Backend Structure

## Directory Organization

### `/agents`
- **`/base`**: Base agent classes that all agents inherit from
- **`/specialized`**: Specialized agent implementations
  - `internal_agent.py`: RAG-based internal knowledge retrieval
  - `web_agent.py`: Real-time web intelligence
- `master_agent_enhanced.py`: LangGraph-based orchestration

### `/api`
- **`/endpoints`**: API route handlers
- **`/middleware`**: Request/response middleware
- **`/schemas`**: Pydantic models for request/response validation

### `/config`
- **`/agents`**: Agent-specific configurations (YAML)
- **`/databases`**: Database connection configurations
- **`/llm`**: LLM provider settings

### `/langchain_config`
- **`/chains`**: LangChain chain definitions
- **`/graphs`**: LangGraph workflow definitions
- **`/prompts`**: Prompt templates
- **`/tools`**: Custom tool implementations

### `/vector_store`
- **`/embeddings`**: Embedding models and cache
- **`/indices`**: Vector database indices
- **`/documents`**: Source documents for RAG

### `/services`
- **`/orchestration`**: Agent coordination logic
- **`/query_processing`**: Query understanding and decomposition
- **`/report_generation`**: Report creation services

### `/tests`
- **`/unit`**: Unit tests for individual components
- **`/integration`**: Integration tests for workflows
- **`/fixtures`**: Test data and mocks

## Key Files

- `master_agent_enhanced.py`: LangGraph-based Master Agent
- `agents/specialized/internal_agent.py`: Internal knowledge RAG agent
- `agents/specialized/web_agent.py`: Web intelligence agent
- `config/agents/agent_config.yaml`: Agent configuration
- `utils/cache/cache_manager.py`: Redis-based caching
- `utils/logging/logger.py`: Structured logging

## Next Steps

1. Implement LangGraph workflows in `/langchain_config/graphs`
2. Set up vector store for internal documents
3. Configure agent prompts in `/langchain_config/prompts`
4. Implement data source connectors
5. Create comprehensive tests
6. Set up monitoring and logging
EOF

echo ""
echo "================================================"
echo "✨ MAESTRO Backend Structure Created Successfully!"
echo "================================================"
echo ""
echo "📋 Summary:"
echo "   - Created enhanced agent architecture with base classes"
echo "   - Added missing agents (Internal Knowledge, Web Intelligence)"
echo "   - Set up LangChain/LangGraph integration structure"
echo "   - Created configuration management system"
echo "   - Added vector store infrastructure for RAG"
echo "   - Set up comprehensive testing structure"
echo "   - Added caching and logging utilities"
echo ""
echo "📝 Next Steps:"
echo "   1. Review the structure: cd ${BACKEND_DIR} && tree"
echo "   2. Install additional requirements: pip install -r requirements_additions.txt"
echo "   3. Configure environment variables in .env"
echo "   4. Implement the TODO sections in agent files"
echo "   5. Set up vector store and load internal documents"
echo ""
echo "📖 Documentation: See ${BACKEND_DIR}/README_STRUCTURE.md"
echo ""