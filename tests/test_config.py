"""Tests for configuration."""
import pytest
from src.config import settings


def test_settings_loaded():
    """Test that settings are loaded."""
    assert settings is not None
    assert hasattr(settings, 'database_url')
    assert hasattr(settings, 'openai_api_key')


def test_database_url():
    """Test database URL is configured."""
    assert settings.database_url is not None
    assert len(settings.database_url) > 0


def test_api_keys():
    """Test API keys are configured."""
    assert settings.openai_api_key is not None
    assert len(settings.openai_api_key) > 0
    assert settings.twilio_account_sid is not None
    assert settings.twilio_auth_token is not None