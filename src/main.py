"""Main FastAPI application."""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting Career Flow AI Agent in {settings.environment} mode")
    yield
    # Shutdown
    logger.info("Shutting down Career Flow AI Agent")


# Create FastAPI app
app = FastAPI(
    title="Career Flow AI Agent",
    description="AI voice agent for career guidance conversations",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Career Flow AI Agent API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment
    }