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
