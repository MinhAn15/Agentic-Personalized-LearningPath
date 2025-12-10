"""
Assessment API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from backend.api.dependencies import get_evaluator_agent

router = APIRouter()


# Request/Response Models
class CreateAssessmentRequest(BaseModel):
    user_id: str
    concept_ids: List[str]
    assessment_type: str = "formative"
    num_questions: int = 5
    time_limit: int = 15


class SubmitAnswerRequest(BaseModel):
    user_id: str
    assessment_id: str
    question_id: str
    answer: Any
    time_spent: int = 0


@router.post("/create", response_model=Dict[str, Any])
async def create_assessment(
    request: CreateAssessmentRequest,
    agent = Depends(get_evaluator_agent)
):
    """Create a new assessment"""
    result = await agent.execute(
        user_id=request.user_id,
        action="create_assessment",
        concept_ids=request.concept_ids,
        assessment_type=request.assessment_type,
        num_questions=request.num_questions,
        time_limit=request.time_limit
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/{assessment_id}/question/{question_index}", response_model=Dict[str, Any])
async def get_question(
    assessment_id: str,
    question_index: int,
    user_id: str,
    agent = Depends(get_evaluator_agent)
):
    """Get a specific question from assessment"""
    result = await agent.execute(
        user_id=user_id,
        action="get_question",
        assessment_id=assessment_id,
        question_index=question_index
    )
    
    return result


@router.post("/submit", response_model=Dict[str, Any])
async def submit_answer(
    request: SubmitAnswerRequest,
    agent = Depends(get_evaluator_agent)
):
    """Submit an answer for a question"""
    result = await agent.execute(
        user_id=request.user_id,
        action="submit_answer",
        assessment_id=request.assessment_id,
        question_id=request.question_id,
        answer=request.answer,
        time_spent=request.time_spent
    )
    
    return result


@router.post("/{assessment_id}/grade", response_model=Dict[str, Any])
async def grade_assessment(
    assessment_id: str,
    user_id: str,
    agent = Depends(get_evaluator_agent)
):
    """Grade complete assessment"""
    result = await agent.execute(
        user_id=user_id,
        action="grade_assessment",
        assessment_id=assessment_id
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/{assessment_id}/feedback", response_model=Dict[str, Any])
async def get_feedback(
    assessment_id: str,
    user_id: str,
    agent = Depends(get_evaluator_agent)
):
    """Get feedback for assessment"""
    result = await agent.execute(
        user_id=user_id,
        action="get_feedback",
        assessment_id=assessment_id
    )
    
    return result


@router.get("/adaptive/{concept_id}", response_model=Dict[str, Any])
async def get_adaptive_question(
    concept_id: str,
    user_id: str,
    current_ability: float = 0.5,
    agent = Depends(get_evaluator_agent)
):
    """Get an adaptive question based on learner ability"""
    result = await agent.execute(
        user_id=user_id,
        action="adaptive_question",
        concept_id=concept_id,
        current_ability=current_ability
    )
    
    return result
