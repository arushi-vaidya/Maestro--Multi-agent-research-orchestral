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
