"""Tests for configuration management."""
import pytest
from src.config.settings import settings


def test_settings_loads_from_env():
    """Test that settings load from environment variables."""
    assert settings.environment in ["development", "staging", "production"]
    assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def test_settings_has_required_keys():
    """Test that all API key fields exist."""
    # These can be None or strings, but attributes must exist
    assert hasattr(settings, "twilio_account_sid")
    assert hasattr(settings, "twilio_auth_token")
    assert hasattr(settings, "twilio_phone_number")
    assert hasattr(settings, "deepgram_api_key")
    assert hasattr(settings, "anthropic_api_key")
    assert hasattr(settings, "elevenlabs_api_key")


def test_settings_defaults():
    """Test default values."""
    assert settings.environment == "development"
    assert settings.log_level == "INFO"