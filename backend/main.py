from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.config import get_settings
from backend.database.database_factory import (
    initialize_databases,
    shutdown_databases,
    get_factory
)

logger = logging.getLogger(__name__)

# Initialization on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("🚀 Starting Agentic Learning Path API...")
    
    # Initialize databases
    if await initialize_databases():
        logger.info("✅ Databases initialized")
    else:
        logger.error("❌ Failed to initialize databases")
        raise RuntimeError("Database initialization failed")
    
    yield
    
    logger.info("🛑 Shutting down...")
    await shutdown_databases()

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

# ============= HEALTH ENDPOINTS =============

@app.get("/health")
async def health_check():
    """System health check"""
    factory = get_factory()
    db_health = await factory.health_check()
    
    all_healthy = all(db_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": settings.API_VERSION,
        "databases": db_health,
        "message": "✅ All systems operational" if all_healthy else "⚠️ Some systems degraded"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🚀 Welcome to Agentic Learning Path API",
        "docs": "/docs",
        "health": "/health",
        "version": settings.API_VERSION
    }

@app.get("/api/v1/system/status")
async def system_status():
    """Detailed system status"""
    factory = get_factory()
    db_health = await factory.health_check()
    
    return {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "version": settings.API_VERSION,
        "databases": {
            "postgres": {
                "status": "healthy" if db_health["postgres"] else "unhealthy",
                "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "unknown"
            },
            "neo4j": {
                "status": "healthy" if db_health["neo4j"] else "unhealthy",
                "url": settings.NEO4J_URI
            },
            "redis": {
                "status": "healthy" if db_health["redis"] else "unhealthy",
                "url": settings.REDIS_URL
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
