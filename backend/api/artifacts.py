"""
Artifacts API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from backend.api.dependencies import get_kag_agent

router = APIRouter()


# Request/Response Models
class GenerateArtifactRequest(BaseModel):
    user_id: str
    artifact_type: str
    concept_ids: List[str]
    concepts_data: Optional[List[Dict[str, Any]]] = None


@router.post("/generate", response_model=Dict[str, Any])
async def generate_artifact(
    request: GenerateArtifactRequest,
    agent = Depends(get_kag_agent)
):
    """Generate a learning artifact"""
    result = await agent.execute(
        user_id=request.user_id,
        action="generate",
        artifact_type=request.artifact_type,
        concept_ids=request.concept_ids,
        concepts_data=request.concepts_data
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/flashcards", response_model=Dict[str, Any])
async def generate_flashcards(
    request: GenerateArtifactRequest,
    cards_per_concept: int = 3,
    agent = Depends(get_kag_agent)
):
    """Generate flashcards for concepts"""
    result = await agent.execute(
        user_id=request.user_id,
        action="generate_flashcards",
        concept_ids=request.concept_ids,
        concepts_data=request.concepts_data,
        cards_per_concept=cards_per_concept
    )
    
    return result


@router.post("/summary", response_model=Dict[str, Any])
async def generate_summary(
    request: GenerateArtifactRequest,
    style: str = "concise",
    agent = Depends(get_kag_agent)
):
    """Generate summary for concepts"""
    result = await agent.execute(
        user_id=request.user_id,
        action="generate_summary",
        concept_ids=request.concept_ids,
        concepts_data=request.concepts_data,
        style=style
    )
    
    return result


@router.post("/mind-map", response_model=Dict[str, Any])
async def generate_mind_map(
    request: GenerateArtifactRequest,
    agent = Depends(get_kag_agent)
):
    """Generate mind map for concepts"""
    result = await agent.execute(
        user_id=request.user_id,
        action="generate_mind_map",
        concept_ids=request.concept_ids,
        concepts_data=request.concepts_data
    )
    
    return result


@router.post("/study-guide", response_model=Dict[str, Any])
async def generate_study_guide(
    request: GenerateArtifactRequest,
    agent = Depends(get_kag_agent)
):
    """Generate study guide for concepts"""
    result = await agent.execute(
        user_id=request.user_id,
        action="generate_study_guide",
        concept_ids=request.concept_ids,
        concepts_data=request.concepts_data
    )
    
    return result


@router.get("/{artifact_id}", response_model=Dict[str, Any])
async def get_artifact(
    artifact_id: str,
    user_id: str,
    agent = Depends(get_kag_agent)
):
    """Get a specific artifact"""
    result = await agent.execute(
        user_id=user_id,
        action="get_artifact",
        artifact_id=artifact_id
    )
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    return result


@router.get("/user/{user_id}", response_model=Dict[str, Any])
async def list_artifacts(
    user_id: str,
    artifact_type: Optional[str] = None,
    agent = Depends(get_kag_agent)
):
    """List artifacts for user"""
    result = await agent.execute(
        user_id=user_id,
        action="list_artifacts",
        artifact_type=artifact_type
    )
    
    return result
