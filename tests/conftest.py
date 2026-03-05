"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient

from healthcare_insurance_platform.core.config import Settings, get_settings
from healthcare_insurance_platform.main import app

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/healthcare_insurance_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        environment="testing",
        database_url=TEST_DATABASE_URL,
        openai_api_key="test_key",
        log_level="DEBUG",
    )


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from healthcare_insurance_platform.db.base import Base
        
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        
        # Drop tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        await engine.dispose()
    except ImportError:
        pytest.skip("Database dependencies not available")


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator:
    """Create test database session."""
    try:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        
        async_session = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        async with async_session() as session:
            yield session
            await session.rollback()
    except ImportError:
        pytest.skip("Database dependencies not available")


@pytest.fixture
def client(test_settings, db_session) -> TestClient:
    """Create test client with overridden dependencies."""
    try:
        from healthcare_insurance_platform.db.base import get_db
        
        async def override_get_db():
            yield db_session
        
        def override_get_settings():
            return test_settings
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_settings] = override_get_settings
        
        with TestClient(app) as test_client:
            yield test_client
        
        app.dependency_overrides.clear()
    except ImportError:
        pytest.skip("Database dependencies not available")


# Pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "property: Property-based tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")

