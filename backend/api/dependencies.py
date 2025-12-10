"""
Dependencies for FastAPI endpoints.

Provides dependency injection for:
- State Manager
- Agents
- Database sessions
"""

from typing import Any
from fastapi import Depends

from backend.database import create_state_manager, get_redis_client, PostgresClient, get_postgres_session
from backend.core import get_event_bus


# ============= STATE MANAGER =============

async def get_state_manager():
    """Dependency to get State Manager"""
    return await create_state_manager()


# ============= AGENTS =============

async def get_path_planner_agent():
    """Get Path Planner Agent instance"""
    from backend.agents import PathPlannerAgent
    
    state_manager = await create_state_manager()
    event_bus = get_event_bus()
    
    return PathPlannerAgent(
        agent_id="path_planner_main",
        state_manager=state_manager,
        event_bus=event_bus
    )


async def get_profiler_agent():
    """Get Profiler Agent instance"""
    from backend.agents import ProfilerAgent
    
    state_manager = await create_state_manager()
    event_bus = get_event_bus()
    
    return ProfilerAgent(
        agent_id="profiler_main",
        state_manager=state_manager,
        event_bus=event_bus
    )


async def get_evaluator_agent():
    """Get Evaluator Agent instance"""
    from backend.agents import EvaluatorAgent
    
    state_manager = await create_state_manager()
    event_bus = get_event_bus()
    
    return EvaluatorAgent(
        agent_id="evaluator_main",
        state_manager=state_manager,
        event_bus=event_bus
    )


async def get_tutor_agent():
    """Get Tutor Agent instance"""
    from backend.agents import TutorAgent
    
    state_manager = await create_state_manager()
    event_bus = get_event_bus()
    
    return TutorAgent(
        agent_id="tutor_main",
        state_manager=state_manager,
        event_bus=event_bus
    )


async def get_kag_agent():
    """Get KAG Agent instance"""
    from backend.agents import KAGAgent
    
    state_manager = await create_state_manager()
    event_bus = get_event_bus()
    
    return KAGAgent(
        agent_id="kag_main",
        state_manager=state_manager,
        event_bus=event_bus
    )


async def get_knowledge_extraction_agent():
    """Get Knowledge Extraction Agent instance"""
    from backend.agents import KnowledgeExtractionAgent
    
    state_manager = await create_state_manager()
    event_bus = get_event_bus()
    
    return KnowledgeExtractionAgent(
        agent_id="knowledge_extraction_main",
        state_manager=state_manager,
        event_bus=event_bus
    )
