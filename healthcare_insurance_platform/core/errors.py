"""Error handling and custom exceptions for the Healthcare Insurance Platform."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from healthcare_insurance_platform.core.logging import get_logger

logger = get_logger(__name__)


class ErrorType(str, Enum):
    """Types of errors that can occur in the platform."""

    VALIDATION = "validation"
    AVAILABILITY = "availability"
    PROCESSING = "processing"
    BUSINESS_LOGIC = "business_logic"
    SECURITY = "security"


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error_code: str
    error_message: str
    error_type: ErrorType
    suggested_action: str
    timestamp: datetime = datetime.utcnow()
    technical_details: Optional[str] = None


class PlatformException(Exception):
    """Base exception for all platform-specific errors."""

    def __init__(
        self,
        error_code: str,
        error_message: str,
        error_type: ErrorType,
        suggested_action: str,
        technical_details: Optional[str] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.error_code = error_code
        self.error_message = error_message
        self.error_type = error_type
        self.suggested_action = suggested_action
        self.technical_details = technical_details
        self.status_code = status_code
        super().__init__(error_message)

    def to_response(self) -> ErrorResponse:
        """Convert exception to error response model."""
        return ErrorResponse(
            error_code=self.error_code,
            error_message=self.error_message,
            error_type=self.error_type,
            suggested_action=self.suggested_action,
            technical_details=self.technical_details if self.technical_details else None,
        )


class ValidationError(PlatformException):
    """Raised when input validation fails."""

    def __init__(self, message: str, technical_details: Optional[str] = None):
        super().__init__(
            error_code="VALIDATION_ERROR",
            error_message=message,
            error_type=ErrorType.VALIDATION,
            suggested_action="Please check your input and try again.",
            technical_details=technical_details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class DataAvailabilityError(PlatformException):
    """Raised when required data is not available."""

    def __init__(self, message: str, technical_details: Optional[str] = None):
        super().__init__(
            error_code="DATA_UNAVAILABLE",
            error_message=message,
            error_type=ErrorType.AVAILABILITY,
            suggested_action="Please try again later or contact support.",
            technical_details=technical_details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class ProcessingError(PlatformException):
    """Raised when processing fails."""

    def __init__(self, message: str, technical_details: Optional[str] = None):
        super().__init__(
            error_code="PROCESSING_ERROR",
            error_message=message,
            error_type=ErrorType.PROCESSING,
            suggested_action="Please try again. If the problem persists, contact support.",
            technical_details=technical_details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class BusinessLogicError(PlatformException):
    """Raised when business logic constraints are violated."""

    def __init__(self, message: str, suggested_action: str, technical_details: Optional[str] = None):
        super().__init__(
            error_code="BUSINESS_LOGIC_ERROR",
            error_message=message,
            error_type=ErrorType.BUSINESS_LOGIC,
            suggested_action=suggested_action,
            technical_details=technical_details,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class SecurityError(PlatformException):
    """Raised when security constraints are violated."""

    def __init__(self, message: str, technical_details: Optional[str] = None):
        super().__init__(
            error_code="SECURITY_ERROR",
            error_message=message,
            error_type=ErrorType.SECURITY,
            suggested_action="Access denied. Please check your permissions.",
            technical_details=technical_details,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class LLMError(PlatformException):
    """Raised when LLM operations fail."""

    def __init__(self, message: str, technical_details: Optional[str] = None):
        super().__init__(
            error_code="LLM_ERROR",
            error_message=message,
            error_type=ErrorType.PROCESSING,
            suggested_action="The AI service encountered an error. Please try again.",
            technical_details=technical_details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class LLMProviderError(PlatformException):
    """Raised when LLM provider initialization or configuration fails."""

    def __init__(self, message: str, technical_details: Optional[str] = None):
        super().__init__(
            error_code="LLM_PROVIDER_ERROR",
            error_message=message,
            error_type=ErrorType.AVAILABILITY,
            suggested_action="The AI service is not properly configured. Please contact support.",
            technical_details=technical_details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


async def platform_exception_handler(request: Request, exc: PlatformException) -> JSONResponse:
    """Handle platform-specific exceptions."""
    logger.error(
        "Platform exception occurred",
        error_code=exc.error_code,
        error_type=exc.error_type.value,
        path=request.url.path,
        technical_details=exc.technical_details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response().model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(
        "Unexpected exception occurred",
        path=request.url.path,
        exception_type=type(exc).__name__,
    )

    error_response = ErrorResponse(
        error_code="INTERNAL_ERROR",
        error_message="An unexpected error occurred. Please try again later.",
        error_type=ErrorType.PROCESSING,
        suggested_action="Please try again. If the problem persists, contact support.",
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )
