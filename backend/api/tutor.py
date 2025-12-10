"""
Tutor API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.api.dependencies import get_tutor_agent

router = APIRouter()


# Request/Response Models
class StartSessionRequest(BaseModel):
    user_id: str
    concept_id: str
    concept_name: str
    learner_profile: Optional[Dict[str, Any]] = None


class AskQuestionRequest(BaseModel):
    user_id: str
    session_id: str
    question: str


class SocraticDialogueRequest(BaseModel):
    user_id: str
    session_id: str
    learner_response: str


@router.post("/session/start", response_model=Dict[str, Any])
async def start_session(
    request: StartSessionRequest,
    agent = Depends(get_tutor_agent)
):
    """Start a new tutoring session"""
    result = await agent.execute(
        user_id=request.user_id,
        action="start_session",
        concept_id=request.concept_id,
        concept_name=request.concept_name,
        learner_profile=request.learner_profile
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/session/{session_id}/content", response_model=Dict[str, Any])
async def get_content(
    session_id: str,
    user_id: str,
    content_type: str = "next",
    agent = Depends(get_tutor_agent)
):
    """Get learning content for session"""
    result = await agent.execute(
        user_id=user_id,
        action="get_content",
        session_id=session_id,
        content_type=content_type
    )
    
    return result


@router.post("/ask", response_model=Dict[str, Any])
async def ask_question(
    request: AskQuestionRequest,
    agent = Depends(get_tutor_agent)
):
    """Ask a question during tutoring"""
    result = await agent.execute(
        user_id=request.user_id,
        action="ask_question",
        session_id=request.session_id,
        question=request.question
    )
    
    return result


@router.get("/session/{session_id}/hint", response_model=Dict[str, Any])
async def get_hint(
    session_id: str,
    user_id: str,
    context: Optional[str] = None,
    agent = Depends(get_tutor_agent)
):
    """Get a hint"""
    result = await agent.execute(
        user_id=user_id,
        action="provide_hint",
        session_id=session_id,
        context=context
    )
    
    return result


@router.get("/explain/{concept_id}", response_model=Dict[str, Any])
async def explain_concept(
    concept_id: str,
    concept_name: str,
    user_id: str,
    depth: str = "standard",
    agent = Depends(get_tutor_agent)
):
    """Get concept explanation"""
    result = await agent.execute(
        user_id=user_id,
        action="explain_concept",
        concept_id=concept_id,
        concept_name=concept_name,
        depth=depth
    )
    
    return result


@router.post("/socratic", response_model=Dict[str, Any])
async def socratic_dialogue(
    request: SocraticDialogueRequest,
    agent = Depends(get_tutor_agent)
):
    """Continue Socratic dialogue"""
    result = await agent.execute(
        user_id=request.user_id,
        action="socratic_dialogue",
        session_id=request.session_id,
        learner_response=request.learner_response
    )
    
    return result


@router.post("/session/{session_id}/end", response_model=Dict[str, Any])
async def end_session(
    session_id: str,
    user_id: str,
    agent = Depends(get_tutor_agent)
):
    """End tutoring session"""
    result = await agent.execute(
        user_id=user_id,
        action="end_session",
        session_id=session_id
    )
    
    return result
