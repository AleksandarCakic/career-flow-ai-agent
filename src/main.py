"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.responses import Response
from contextlib import asynccontextmanager
from src.config.settings import settings
from src.api.routes import webhooks, deepgram, voice_pipeline
import logging
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware

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
    lifespan=lifespan,
    docs_url="/docs",   
    redoc_url="/redoc"
)

# Add CORS middleware BEFORE routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers AFTER middleware
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(deepgram.router, prefix="/deepgram", tags=["Deepgram"])
app.include_router(voice_pipeline.router, prefix="/voice-pipeline", tags=["Voice Pipeline"])


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