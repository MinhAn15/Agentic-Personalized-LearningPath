"""
Profile API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from backend.api.dependencies import get_profiler_agent

router = APIRouter()


# Request/Response Models
class CreateProfileRequest(BaseModel):
    user_id: str
    name: str


class UpdateKnowledgeRequest(BaseModel):
    user_id: str
    concept_id: str
    concept_name: str
    skill_level: str
    confidence: float


class UpdatePreferencesRequest(BaseModel):
    user_id: str
    preferences: Dict[str, Any]


class ProfileResponse(BaseModel):
    status: str
    profile: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


@router.post("/create", response_model=ProfileResponse)
async def create_profile(
    request: CreateProfileRequest,
    agent = Depends(get_profiler_agent)
):
    """Create or get learner profile"""
    result = await agent.execute(
        user_id=request.user_id,
        action="get_profile",
        name=request.name
    )
    
    return ProfileResponse(**result)


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: str,
    agent = Depends(get_profiler_agent)
):
    """Get learner profile"""
    result = await agent.execute(
        user_id=user_id,
        action="get_profile"
    )
    
    return ProfileResponse(**result)


@router.post("/knowledge", response_model=Dict[str, Any])
async def update_knowledge(
    request: UpdateKnowledgeRequest,
    agent = Depends(get_profiler_agent)
):
    """Update knowledge state for a concept"""
    result = await agent.execute(
        user_id=request.user_id,
        action="update_knowledge",
        concept_id=request.concept_id,
        concept_name=request.concept_name,
        skill_level=request.skill_level,
        confidence=request.confidence
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/{user_id}/gaps", response_model=Dict[str, Any])
async def analyze_gaps(
    user_id: str,
    agent = Depends(get_profiler_agent)
):
    """Analyze knowledge gaps for learner"""
    result = await agent.execute(
        user_id=user_id,
        action="analyze_gaps"
    )
    
    return result


@router.get("/{user_id}/learning-style", response_model=Dict[str, Any])
async def assess_learning_style(
    user_id: str,
    agent = Depends(get_profiler_agent)
):
    """Assess learner's learning style"""
    result = await agent.execute(
        user_id=user_id,
        action="assess_style"
    )
    
    return result


@router.post("/preferences", response_model=Dict[str, Any])
async def update_preferences(
    request: UpdatePreferencesRequest,
    agent = Depends(get_profiler_agent)
):
    """Update learner preferences"""
    result = await agent.execute(
        user_id=request.user_id,
        action="update_preferences",
        preferences=request.preferences
    )
    
    return result
