from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.config import get_settings

logger = logging.getLogger(__name__)

# Initialization on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("🚀 Starting Agentic Learning Path API...")
    # Startup code
    yield
    logger.info("🛑 Shutting down...")
    # Cleanup code

# Create FastAPI app
app = FastAPI(
    title="Agentic Learning Path API",
    description="Multi-Agent AI system for personalized learning paths",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "message": "✅ Agentic Learning Path API is running"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "🚀 Welcome to Agentic Learning Path API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
