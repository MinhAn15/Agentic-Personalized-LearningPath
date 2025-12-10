"""
API routes for multi-agent system
"""

from .agent_routes import router as agents_router, set_agents
from .path_routes import router as paths_router, set_path_planner_agent

__all__ = ["agents_router", "paths_router", "set_agents", "set_path_planner_agent"]
