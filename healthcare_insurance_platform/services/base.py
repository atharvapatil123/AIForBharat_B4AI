"""Base service class for all platform services."""

from abc import ABC
from typing import Optional, TYPE_CHECKING

from healthcare_insurance_platform.core.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from healthcare_insurance_platform.db.vector_store import VectorStore


class BaseService(ABC):
    """Base class for all services in the platform.
    
    Provides common functionality like logging, database access,
    and vector store access.
    """

    def __init__(
        self,
        db: Optional["AsyncSession"] = None,
        vector_store: Optional["VectorStore"] = None,
    ):
        """Initialize base service.
        
        Args:
            db: Database session for structured data access
            vector_store: Vector store for policy document retrieval
        """
        self.db = db
        self.vector_store = vector_store
        self.logger = get_logger(self.__class__.__name__)

    def _log_operation(self, operation: str, **kwargs) -> None:
        """Log service operation with context."""
        self.logger.info(f"Service operation: {operation}", **kwargs)

    def _log_error(self, operation: str, error: Exception, **kwargs) -> None:
        """Log service error with context."""
        self.logger.error(
            f"Service error: {operation}",
            error=str(error),
            error_type=type(error).__name__,
            **kwargs,
        )
