"""
Learning Path API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from backend.api.dependencies import get_path_planner_agent

router = APIRouter()


# Request/Response Models
class GeneratePathRequest(BaseModel):
    user_id: str
    goal: str
    concepts: List[Dict[str, Any]]
    time_budget: Optional[int] = None  # minutes


class UpdatePathRequest(BaseModel):
    path_id: str
    node_id: str
    status: str


class PathResponse(BaseModel):
    status: str
    path: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


@router.post("/generate", response_model=PathResponse)
async def generate_learning_path(
    request: GeneratePathRequest,
    agent = Depends(get_path_planner_agent)
):
    """
    Generate a personalized learning path.
    
    - **user_id**: Unique identifier for the learner
    - **goal**: Learning goal description
    - **concepts**: List of concepts to include
    - **time_budget**: Optional time constraint in minutes
    """
    result = await agent.execute(
        user_id=request.user_id,
        action="generate_path",
        goal=request.goal,
        concepts=request.concepts,
        time_budget=request.time_budget
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return PathResponse(**result)


@router.get("/{user_id}", response_model=PathResponse)
async def get_learning_path(
    user_id: str,
    path_id: Optional[str] = None,
    agent = Depends(get_path_planner_agent)
):
    """Get current learning path for user"""
    result = await agent.execute(
        user_id=user_id,
        action="get_path",
        path_id=path_id
    )
    
    return PathResponse(**result)


@router.post("/update", response_model=PathResponse)
async def update_path_node(
    request: UpdatePathRequest,
    agent = Depends(get_path_planner_agent)
):
    """Update a node status in the learning path"""
    result = await agent.execute(
        user_id="",
        action="update_path",
        path_id=request.path_id,
        node_id=request.node_id,
        status=request.status
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return PathResponse(**result)


@router.get("/{user_id}/next", response_model=Dict[str, Any])
async def get_next_node(
    user_id: str,
    path_id: Optional[str] = None,
    agent = Depends(get_path_planner_agent)
):
    """Get the next node to learn"""
    result = await agent.execute(
        user_id=user_id,
        action="get_next_node",
        path_id=path_id
    )
    
    return result
