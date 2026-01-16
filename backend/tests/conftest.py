"""
Pytest fixtures for AI Task Agent backend tests.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database."""
    # Use in-memory SQLite for tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    yield TestingSessionLocal

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Get a database session for a test."""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecureP@ssw0rd123!"
    }


@pytest.fixture
def sample_workflow_data():
    """Sample workflow definition."""
    return {
        "id": "test-workflow-1",
        "name": "Test Workflow",
        "description": "A test workflow",
        "steps": [
            {
                "id": "step1",
                "name": "First Step",
                "type": "tool",
                "config": {
                    "tool": "calculator",
                    "operation": "add",
                    "a": 5,
                    "b": 3
                }
            }
        ]
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("JWT_SECRET", "test-secret-key-for-testing-only")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
