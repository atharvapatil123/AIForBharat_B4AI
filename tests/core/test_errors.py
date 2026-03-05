"""Tests for error handling."""

import pytest

from healthcare_insurance_platform.core.errors import (
    BusinessLogicError,
    DataAvailabilityError,
    ErrorType,
    ProcessingError,
    SecurityError,
    ValidationError,
)


@pytest.mark.unit
def test_validation_error():
    """Test ValidationError creation and response."""
    error = ValidationError("Invalid input", technical_details="Field X is required")
    assert error.error_code == "VALIDATION_ERROR"
    assert error.error_type == ErrorType.VALIDATION
    assert error.status_code == 422

    response = error.to_response()
    assert response.error_code == "VALIDATION_ERROR"
    assert response.error_message == "Invalid input"
    assert response.technical_details == "Field X is required"


@pytest.mark.unit
def test_data_availability_error():
    """Test DataAvailabilityError creation."""
    error = DataAvailabilityError("Policy not found")
    assert error.error_code == "DATA_UNAVAILABLE"
    assert error.error_type == ErrorType.AVAILABILITY
    assert error.status_code == 503


@pytest.mark.unit
def test_processing_error():
    """Test ProcessingError creation."""
    error = ProcessingError("LLM generation failed")
    assert error.error_code == "PROCESSING_ERROR"
    assert error.error_type == ErrorType.PROCESSING
    assert error.status_code == 500


@pytest.mark.unit
def test_business_logic_error():
    """Test BusinessLogicError creation."""
    error = BusinessLogicError(
        "Claim amount exceeds limit",
        suggested_action="Reduce claim amount or split into multiple claims",
    )
    assert error.error_code == "BUSINESS_LOGIC_ERROR"
    assert error.error_type == ErrorType.BUSINESS_LOGIC
    assert error.status_code == 400


@pytest.mark.unit
def test_security_error():
    """Test SecurityError creation."""
    error = SecurityError("Unauthorized access attempt")
    assert error.error_code == "SECURITY_ERROR"
    assert error.error_type == ErrorType.SECURITY
    assert error.status_code == 403
