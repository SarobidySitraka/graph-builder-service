"""Pytest configuration and fixtures."""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.config import settings
from app.api.dependencies import get_session_manager
from app.services.session_manager2 import SessionManager


# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Test Client Fixtures
# ============================================================================

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create test client for synchronous tests.

    Usage:
        def test_endpoint(client):
            response = client.get("/health")
            assert response.status_code == 200
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create async test client for asynchronous tests.

    Usage:
        async def test_endpoint(async_client):
            response = await async_client.get("/health")
            assert response.status_code == 200
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Session Manager Fixtures
# ============================================================================

@pytest.fixture
def session_manager() -> SessionManager:
    """
    Create test session manager with temporary cache.

    Usage:
        def test_session_creation(session_manager):
            session_id = session_manager.create_session(...)
            assert session_id is not None
    """
    import tempfile
    import shutil

    # Create temporary directory for test cache
    temp_dir = tempfile.mkdtemp()

    # Create session manager with test configuration
    manager = SessionManager(
        cache_dir=temp_dir,
        session_timeout=300  # 5 minutes for tests
    )

    yield manager

    # Cleanup
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


@pytest.fixture
def override_session_manager(session_manager):
    """
    Override session manager dependency for testing.

    Usage:
        def test_with_override(client, override_session_manager):
            response = client.get("/api/v1/sessions")
            # Uses test session manager
    """
    app.dependency_overrides[get_session_manager] = lambda: session_manager
    yield
    app.dependency_overrides.clear()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_csv_content() -> str:
    """Sample CSV content for file upload tests."""
    return """id,name,age,city
1,John Doe,30,New York
2,Jane Smith,25,Los Angeles
3,Bob Johnson,35,Chicago"""


@pytest.fixture
def sample_graph_config() -> list:
    """Sample graph configuration for testing."""
    return [
        {
            "source": {
                "label": "Person",
                "properties": ["id", "name", "age"]
            },
            "target": {
                "label": "City",
                "properties": ["city"]
            },
            "rels": {
                "label": "LIVES_IN",
                "properties": []
            }
        }
    ]


@pytest.fixture
def sample_db_config() -> dict:
    """Sample database configuration for testing."""
    return {
        "db_type": "mysql",
        "host": "localhost",
        "port": 3306,
        "db": "test_db",
        "user": "test_user",
        "password": "test_password"
    }


# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def mock_dataframes():
    """Mock polars dataframes for testing."""
    import polars as pl

    return {
        "users": pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["John", "Jane", "Bob"],
            "age": [30, 25, 35]
        }),
        "cities": pl.DataFrame({
            "city": ["New York", "Los Angeles", "Chicago"],
            "country": ["USA", "USA", "USA"]
        })
    }


@pytest.fixture
def mock_table_data():
    """Mock table metadata for testing."""
    return {
        "users": {
            "table_name": "users",
            "columns": ["id", "name", "age"],
            "total_rows": 3,
            "total_columns": 3,
            "preview": [
                {"id": 1, "name": "John", "age": 30},
                {"id": 2, "name": "Jane", "age": 25},
            ]
        }
    }


# ============================================================================
# Neo4j Test Fixtures
# ============================================================================

@pytest.fixture
def mock_neo4j_driver(mocker):
    """Mock Neo4j driver for testing without actual database."""
    mock_driver = mocker.Mock()
    mock_driver.verify_connectivity.return_value = True
    return mock_driver


# ============================================================================
# Environment Configuration
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Configure test environment."""
    import os

    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "true"

    # Use test database
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_USERNAME"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "test"

    yield

    # Cleanup is automatic


# ============================================================================
# Markers
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "neo4j: marks tests that require Neo4j connection"
    )