"""
Pytest Configuration and Global Fixtures
Shared fixtures for all tests
"""
import pytest
import sys
import os
from pathlib import Path

# Add backend directory to Python path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import all fixtures from fixtures directory
from tests.fixtures.agent_fixtures import *

# Global test configuration
pytest_plugins = []


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before running tests"""
    # Disable any real API calls
    os.environ["TESTING"] = "true"

    yield

    # Cleanup after all tests
    pass


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks between tests"""
    yield
    # Cleanup happens automatically with pytest


# Configure pytest markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
