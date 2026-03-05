"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from healthcare_insurance_platform.core.config import get_settings
from healthcare_insurance_platform.core.errors import (
    PlatformException,
    general_exception_handler,
    platform_exception_handler,
)
from healthcare_insurance_platform.core.logging import get_logger, setup_logging
from healthcare_insurance_platform.db.base import close_db, init_db
from healthcare_insurance_platform.db.vector_store import close_vector_store, get_vector_store

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Healthcare Insurance Intelligence Platform")
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")

    # Initialize database
    await init_db()

    # Initialize vector store
    get_vector_store()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Healthcare Insurance Intelligence Platform")

    # Close database connections
    await close_db()

    # Close vector store
    close_vector_store()

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Healthcare Insurance Intelligence Platform",
    description="A multilingual AI-powered system for health insurance guidance",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(PlatformException, platform_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "status": "healthy",
        "service": "Healthcare Insurance Intelligence Platform",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
    }


# Import and include routers here as they are created
# from healthcare_insurance_platform.api import policy_router, claim_router
# app.include_router(policy_router, prefix="/api/v1/policies", tags=["policies"])
# app.include_router(claim_router, prefix="/api/v1/claims", tags=["claims"])
