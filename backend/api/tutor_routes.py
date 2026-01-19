from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tutoring", tags=["tutoring"])

from backend.models.schemas import TutorInput

# Global agent instance
_tutor_agent = None

def set_tutor_agent(agent):
    """Set tutor agent instance"""
    global _tutor_agent
    _tutor_agent = agent

class TutorResponse(BaseModel):
    """Tutor's response to learner question"""
    success: bool
    guidance: str
    hint_level: int
    follow_up_question: Optional[str]
    source: str
    execution_time_ms: float

@router.post("/ask")
async def ask_tutor(request: TutorInput) -> TutorResponse:
    """
    Ask tutor for help with a concept.
    
    This endpoint:
    1. Retrieves concept details from KG
    2. Gets learner's current mastery
    3. Retrieves relevant course materials (RAG)
    4. Generates Socratic guidance (no direct answers)
    5. Returns guidance following Harvard 7 Principles
    
    Example request:
    {
        "learner_id": "user_123",
        "question": "What does WHERE do in SQL?",
        "concept_id": "SQL_WHERE",
        "hint_level": 1,
        "force_real": false
    }
    
    Example response:
    {
        "success": true,
        "guidance": "Great question! Think about it this way:
                    Imagine you have 1000 records but only want 
                    people over 21. What would you do first?",
        "hint_level": 1,
        "follow_up_question": "What do you think WHERE does then?",
        "source": "Course Materials",
        "execution_time_ms": 1234.5
    }
    """
    try:
        if not _tutor_agent:
            raise HTTPException(status_code=500, detail="Tutor Agent not initialized")
        
        start_time = time.time()
        
        result = await _tutor_agent.execute(
            learner_id=request.learner_id,
            question=request.question,
            concept_id=request.concept_id,
            hint_level=request.hint_level,
            conversation_history=request.conversation_history or [],
            force_real=request.force_real
        )
        
        execution_time = (time.time() - start_time) * 1000  # ms
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return TutorResponse(
            success=result.get("success", False),
            guidance=result.get("guidance", ""),
            hint_level=result.get("hint_level", 1),
            follow_up_question=result.get("follow_up_question"),
            source=result.get("source", ""),
            execution_time_ms=execution_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tutor endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/concept/{concept_id}")
async def get_concept_help(learner_id: str, concept_id: str):
    """
    Get general help on a concept (no specific question).
    
    Returns overview + learning suggestions.
    """
    try:
        if not _tutor_agent:
            raise HTTPException(status_code=500, detail="Tutor Agent not initialized")
        
        # Get concept from KG
        neo4j = _tutor_agent.state_manager.neo4j
        concept_result = await neo4j.run_query(
            "MATCH (c:CourseConcept {concept_id: $concept_id}) RETURN c",
            concept_id=concept_id
        )
        
        if not concept_result:
            raise HTTPException(status_code=404, detail=f"Concept not found: {concept_id}")
        
        concept = concept_result[0].get("c", {})
        
        return {
            "success": True,
            "concept": concept,
            "message": f"What would you like to know about {concept.get('name')}?",
            "ask_url": "/api/v1/tutoring/ask"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get concept error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/increase-hint")
async def increase_hint(request: TutorInput):
    """
    Request more detailed guidance (increase hint level).
    
    Use this if Socratic guidance is too vague.
    """
    try:
        # Increase hint level (max 5)
        new_hint = min(request.hint_level + 1, 5)
        
        request.hint_level = new_hint
        
        # Re-ask with higher hint level
        return await ask_tutor(request)
    
    except Exception as e:
        logger.error(f"Increase hint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decrease-hint")
async def decrease_hint(request: TutorInput):
    """
    Request less guidance (decrease hint level).
    
    Use this if you want to struggle more and learn better.
    """
    try:
        # Decrease hint level (min 0)
        new_hint = max(request.hint_level - 1, 0)
        
        request.hint_level = new_hint
        
        # Re-ask with lower hint level
        return await ask_tutor(request)
    
    except Exception as e:
        logger.error(f"Decrease hint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/principles")
async def get_principles():
    """
    Get the Harvard 7 Pedagogical Principles this tutor follows.
    """
    return {
        "principles": [
            "1. Never give direct answers - guide with questions",
            "2. Keep responses SHORT (2-4 sentences max)",
            "3. Reveal ONE STEP AT A TIME",
            "4. Ask 'What do YOU think?' before helping",
            "5. Praise EFFORT, not intelligence",
            "6. Personalized feedback for THEIR specific error",
            "7. Ground ONLY in verified sources (RAG + KG)"
        ],
        "source": "Kestin et al. (2025) - Effective Teaching Practices",
        "hint_levels": {
            "0": "No hints - let them struggle (productive struggle)",
            "1": "Gentle guidance - What do you think?",
            "2": "Clarifying questions",
            "3": "Partial example",
            "4": "Full explanation",
            "5": "Direct answer (last resort)"
        }
    }
