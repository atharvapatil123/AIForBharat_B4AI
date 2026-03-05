"""Tests for configuration management."""

import pytest

from healthcare_insurance_platform.core.config import Settings


@pytest.mark.unit
def test_settings_defaults():
    """Test default settings values."""
    settings = Settings(openai_api_key="test_key")
    assert settings.environment == "development"
    assert settings.api_port == 8000
    assert settings.log_level == "INFO"


@pytest.mark.unit
def test_settings_environment_properties():
    """Test environment property helpers."""
    dev_settings = Settings(environment="development", openai_api_key="test_key")
    assert dev_settings.is_development is True
    assert dev_settings.is_production is False
    assert dev_settings.is_testing is False

    prod_settings = Settings(environment="production", openai_api_key="test_key")
    assert prod_settings.is_development is False
    assert prod_settings.is_production is True
    assert prod_settings.is_testing is False


@pytest.mark.unit
def test_settings_validation():
    """Test settings validation."""
    with pytest.raises(ValueError, match="OpenAI API key must be set"):
        Settings(openai_api_key="")
