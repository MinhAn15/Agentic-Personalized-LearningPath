"""
API routes for multi-agent system
"""

from .agent_routes import router as agents_router, set_agents
from .path_routes import router as paths_router, set_path_planner_agent
from .tutor_routes import router as tutor_router, set_tutor_agent
from .evaluator_routes import router as evaluator_router, set_evaluator_agent
from .kag_routes import router as kag_router, set_kag_agent

__all__ = [
    "agents_router", 
    "paths_router", 
    "tutor_router",
    "evaluator_router",
    "kag_router",
    "set_agents", 
    "set_path_planner_agent",
    "set_tutor_agent",
    "set_evaluator_agent",
    "set_kag_agent"
]
