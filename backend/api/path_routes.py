from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/paths", tags=["paths"])

# Global agent instance
_path_planner_agent = None

def set_path_planner_agent(agent):
    """Set path planner agent instance"""
    global _path_planner_agent
    _path_planner_agent = agent

class PlanPathRequest(BaseModel):
    """Request to plan learning path"""
    learner_id: str
    goal: Optional[str] = None

@router.post("/plan")
async def plan_learning_path(request: PlanPathRequest):
    """
    Plan optimal learning path for a learner.
    
    This endpoint:
    1. Gets learner profile
    2. Gets Course KG from Neo4j
    3. Uses RL to select optimal concept sequence
    4. Generates day-by-day path with resource recommendations
    
    Example request:
    {
        "learner_id": "user_123",
        "goal": "Master SQL JOINs"
    }
    
    Example response:
    {
        "success": true,
        "learner_id": "user_123",
        "learning_path": [
            {
                "day": 1,
                "concept": "SQL_WHERE",
                "difficulty": 2,
                "estimated_hours": 4
            },
            ...
        ],
        "pacing": "MODERATE",
        "success_probability": 0.92
    }
    """
    try:
        if not _path_planner_agent:
            raise HTTPException(status_code=500, detail="Path Planner Agent not initialized")
        
        start_time = time.time()
        
        result = await _path_planner_agent.execute(
            learner_id=request.learner_id,
            goal=request.goal
        )
        
        execution_time = (time.time() - start_time) * 1000  # ms
        
        return {
            "success": result.get("success", False),
            "execution_time_ms": execution_time,
            "result": result,
            "error": result.get("error")
        }
    
    except Exception as e:
        logger.error(f"Path planning endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learner/{learner_id}")
async def get_learner_path(learner_id: str):
    """
    Get previously planned learning path for a learner.
    
    Returns cached path if available.
    """
    try:
        if not _path_planner_agent:
            raise HTTPException(status_code=500, detail="Path Planner Agent not initialized")
        
        path = await _path_planner_agent.state_manager.get(f"path:{learner_id}")
        
        if not path:
            raise HTTPException(status_code=404, detail=f"No path found for learner {learner_id}")
        
        return {
            "success": True,
            "learner_id": learner_id,
            "path": path
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get path endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
