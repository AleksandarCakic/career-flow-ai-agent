import pytest
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env file before any imports
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Set environment variables before any imports
os.environ.setdefault("TWILIO_ACCOUNT_SID", "test_sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test_token")
os.environ.setdefault("TWILIO_PHONE_NUMBER", "test_phone")
os.environ.setdefault("DEEPGRAM_API_KEY", "test_deepgram_key")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")
os.environ.setdefault("ELEVENLABS_API_KEY", "test_elevenlabs_key")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("SERVER_HOST", "0.0.0.0")
os.environ.setdefault("SERVER_PORT", "8000")

@pytest.fixture
def client():
    """Test client fixture for FastAPI app."""
    from fastapi.testclient import TestClient
    from src.main import app
    return TestClient(app)