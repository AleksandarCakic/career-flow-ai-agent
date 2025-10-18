"""Configuration management using Pydantic settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Twilio Configuration
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # Deepgram (Speech-to-Text)
    deepgram_api_key: Optional[str] = None
    
    # Anthropic (Claude AI)
    anthropic_api_key: Optional[str] = None
    
    # ElevenLabs (Text-to-Speech)
    elevenlabs_api_key: Optional[str] = None
    
    # Application Settings
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()