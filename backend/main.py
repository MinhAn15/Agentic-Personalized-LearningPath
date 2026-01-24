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
from backend.agents import (
    KnowledgeExtractionAgent,
    ProfilerAgent,
    PathPlannerAgent,
    TutorAgent,
    EvaluatorAgent,
    KAGAgent
)
from backend.core import CentralStateManager, EventBus
from backend.api.agent_routes import router as agents_router, set_agents
from backend.api.path_routes import router as paths_router, set_path_planner_agent
from backend.api.tutor_routes import router as tutor_router, set_tutor_agent
from backend.api.evaluator_routes import router as evaluator_router, set_evaluator_agent
from backend.api.kag_routes import router as kag_router, set_kag_agent

logger = logging.getLogger(__name__)

# Global variables
_state_manager = None
_event_bus = None
_agents = {}

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
    
    # Initialize infrastructure
    factory = get_factory()
    global _state_manager, _event_bus
    _state_manager = CentralStateManager(factory.redis, factory.postgres)
    _state_manager.neo4j = factory.neo4j  # Add neo4j to state_manager
    _event_bus = EventBus()
    
    logger.info("✅ Infrastructure initialized")
    
    # Initialize agents
    try:
        ke_agent = KnowledgeExtractionAgent(
            agent_id="knowledge_extraction_1",
            state_manager=_state_manager,
            event_bus=_event_bus
        )
        
        profiler_agent = ProfilerAgent(
            agent_id="profiler_1",
            state_manager=_state_manager,
            event_bus=_event_bus
        )
        
        path_planner_agent = PathPlannerAgent(
            agent_id="path_planner_1",
            state_manager=_state_manager,
            event_bus=_event_bus
        )
        
        tutor_agent = TutorAgent(
            agent_id="tutor_1",
            state_manager=_state_manager,
            event_bus=_event_bus
        )
        
        evaluator_agent = EvaluatorAgent(
            agent_id="evaluator_1",
            state_manager=_state_manager,
            event_bus=_event_bus
        )
        
        kag_agent = KAGAgent(
            agent_id="kag_1",
            state_manager=_state_manager,
            event_bus=_event_bus
        )
        
        _agents["knowledge_extraction"] = ke_agent
        _agents["profiler"] = profiler_agent
        _agents["path_planner"] = path_planner_agent
        _agents["tutor"] = tutor_agent
        _agents["evaluator"] = evaluator_agent
        _agents["kag"] = kag_agent
        
        # Set agents in routes
        set_agents(ke_agent, profiler_agent)
        set_path_planner_agent(path_planner_agent)
        set_tutor_agent(tutor_agent)
        set_evaluator_agent(evaluator_agent)
        set_kag_agent(kag_agent)
        
        logger.info("✅ Agents initialized (KE, Profiler, PathPlanner, Tutor, Evaluator, KAG)")
    except Exception as e:
        logger.error(f"❌ Agent initialization failed: {e}")
        raise RuntimeError("Agent initialization failed")
    
    yield
    
    logger.info("🛑 Shutting down...")
    await shutdown_databases()

# Create FastAPI app
app = FastAPI(
    title="Agentic Learning Path API",
    description="Multi-Agent AI system for personalized learning paths",
    version="0.2.0",
    lifespan=lifespan
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router)
app.include_router(paths_router)
app.include_router(tutor_router)
app.include_router(evaluator_router)
app.include_router(kag_router)

from backend.api.admin_routes import router as admin_router
app.include_router(admin_router)
from backend.api.learner_routes import router as learner_router
app.include_router(learner_router)

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
        "agents": {
            "knowledge_extraction": "knowledge_extraction" in _agents,
            "profiler": "profiler" in _agents,
            "path_planner": "path_planner" in _agents,
            "tutor": "tutor" in _agents,
            "evaluator": "evaluator" in _agents,
            "kag": "kag" in _agents
        },
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
        },
        "agents": {
            "knowledge_extraction": "knowledge_extraction" in _agents,
            "profiler": "profiler" in _agents,
            "path_planner": "path_planner" in _agents,
            "tutor": "tutor" in _agents,
            "evaluator": "evaluator" in _agents,
            "kag": "kag" in _agents
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
