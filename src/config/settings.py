"""Configuration management using Pydantic settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    deepgram_api_key: str
    anthropic_api_key: str
    elevenlabs_api_key: str
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

settings = Settings() # type: ignore