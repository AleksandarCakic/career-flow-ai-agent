"""Application configuration."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys - Required
    openai_api_key: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    
    # API Keys - Optional (for old integrations)
    deepgram_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    
    # Database
    database_url: str
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    environment: str = "development"
    log_level: str = "INFO"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra fields in .env
    }


settings = Settings() # type: ignore