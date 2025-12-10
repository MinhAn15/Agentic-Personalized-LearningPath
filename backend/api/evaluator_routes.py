from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])

_evaluator_agent = None

def set_evaluator_agent(agent):
    """Set evaluator agent instance"""
    global _evaluator_agent
    _evaluator_agent = agent

class EvaluationRequest(BaseModel):
    """Request to evaluate learner response"""
    learner_id: str
    concept_id: str
    learner_response: str
    expected_answer: str
    correct_answer_explanation: Optional[str] = None

class EvaluationResponse(BaseModel):
    """Evaluation result"""
    success: bool
    learner_id: str
    concept_id: str
    score: float  # 0-1
    error_type: str
    misconception: Optional[str]
    feedback: str
    decision: str
    new_mastery: float
    execution_time_ms: float

@router.post("/evaluate")
async def evaluate_response(request: EvaluationRequest) -> EvaluationResponse:
    """
    Evaluate learner response.
    
    This endpoint:
    1. Scores response (0-1)
    2. Classifies error type (CORRECT, CARELESS, INCOMPLETE, PROCEDURAL, CONCEPTUAL)
    3. Detects misconceptions
    4. Generates personalized feedback
    5. Makes path decision (PROCEED/REMEDIATE/ALTERNATE/MASTERED)
    6. Updates learner progress
    
    Example request:
    {
        "learner_id": "user_123",
        "concept_id": "SQL_WHERE",
        "learner_response": "WHERE combines two tables",
        "expected_answer": "WHERE filters rows",
        "correct_answer_explanation": "WHERE filters rows based on conditions"
    }
    
    Example response:
    {
        "success": true,
        "score": 0.2,
        "error_type": "CONCEPTUAL",
        "misconception": "Confuses WHERE with JOIN",
        "feedback": "I see the confusion - WHERE filters, JOIN combines...",
        "decision": "REMEDIATE",
        "new_mastery": 0.35
    }
    """
    try:
        if not _evaluator_agent:
            raise HTTPException(status_code=500, detail="Evaluator Agent not initialized")
        
        start_time = time.time()
        
        result = await _evaluator_agent.execute(
            learner_id=request.learner_id,
            concept_id=request.concept_id,
            learner_response=request.learner_response,
            expected_answer=request.expected_answer,
            correct_answer_explanation=request.correct_answer_explanation
        )
        
        execution_time = (time.time() - start_time) * 1000  # ms
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return EvaluationResponse(
            success=result.get("success", False),
            learner_id=result.get("learner_id", ""),
            concept_id=result.get("concept_id", ""),
            score=result.get("score", 0.0),
            error_type=result.get("error_type", ""),
            misconception=result.get("misconception"),
            feedback=result.get("feedback", ""),
            decision=result.get("decision", ""),
            new_mastery=result.get("new_mastery", 0.0),
            execution_time_ms=execution_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/error-types")
async def get_error_types():
    """Get supported error classifications"""
    return {
        "error_types": [
            "CORRECT",
            "CARELESS",
            "INCOMPLETE",
            "PROCEDURAL",
            "CONCEPTUAL"
        ],
        "path_decisions": [
            "PROCEED",
            "REMEDIATE",
            "ALTERNATE",
            "MASTERED"
        ]
    }
