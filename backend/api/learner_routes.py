from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from backend.core.state_manager import CentralStateManager
from backend.database.database_factory import get_factory

router = APIRouter(prefix="/api/v1/learners", tags=["Learners"])
logger = logging.getLogger(__name__)

# --- Schemas ---
class LearnerSignupRequest(BaseModel):
    name: str
    email: EmailStr
    age: int
    background: str  # e.g., "Student", "Professional"
    consent_agreed: bool

class LearnerProfileResponse(BaseModel):
    learner_id: str
    name: str
    cohort: str  # "TREATMENT" or "CONTROL"
    created_at: datetime

class PreTestSubmission(BaseModel):
    learner_id: str
    answers: Dict[str, Any]  # { "q1": "a", "q2": "c" }

# --- Dependencies ---
async def get_state_manager():
    factory = get_factory()
    return CentralStateManager(factory.redis, factory.postgres)

# --- Routes ---

@router.post("/signup", response_model=LearnerProfileResponse)
async def signup_learner(
    request: LearnerSignupRequest,
    state_manager: CentralStateManager = Depends(get_state_manager)
):
    """
    Register a new learner for the pilot.
    Assign to COHORT (A/B testing) automatically.
    """
    if not request.consent_agreed:
        raise HTTPException(status_code=400, detail="Consent is required")
    
    learner_id = str(uuid.uuid4())
    
    # Assign Cohort (Simple Random Assignment)
    # In production, use ExperimentManager for proper balance
    import random
    cohort = "TREATMENT" if random.random() < 0.5 else "CONTROL"
    
    profile = {
        "learner_id": learner_id,
        "name": request.name,
        "email": request.email,
        "age": request.age,
        "background": request.background,
        "cohort": cohort,
        "created_at": datetime.now().isoformat(),
        "status": "ONBOARDING"
    }
    
    # Save to Redis/DB (via StateManager)
    # Note: StateManager needs a method to save generic profile. 
    # For now we use the postgres client directly if available or extend state manager.
    # Assuming state_manager has access to underlying DB.
    try:
        # Save to Postgres via wrapper (mocked here if method missing)
        if hasattr(state_manager.postgres, "create_learner"):
            await state_manager.postgres.create_learner(profile)
        
        # Cache profile
        await state_manager.set(f"profile:{learner_id}", profile)
        
        logger.info(f"Learner {learner_id} signed up. Cohort: {cohort}")
        
    except Exception as e:
        logger.error(f"Signup failed: {e}")
        raise HTTPException(status_code=500, detail="Signup failed")
    
    return LearnerProfileResponse(
        learner_id=learner_id,
        name=request.name,
        cohort=cohort,
        created_at=profile["created_at"]
    )

@router.post("/pre-test")
async def submit_pre_test(
    submission: PreTestSubmission,
    state_manager: CentralStateManager = Depends(get_state_manager)
):
    """
    Submit pre-test answers. Calculates score and updates profile.
    """
    # 1. Calculate Score (Mock logic)
    # In real impl, would load Answer Key from KG/DB
    correct_count = 0
    total_questions = len(submission.answers)
    
    # Mock grading
    for q_id, answer in submission.answers.items():
        if answer == "correct": # Placeholder
            correct_count += 1
            
    score = (correct_count / total_questions) * 10 if total_questions > 0 else 0
    
    # 2. Update Profile
    profile = await state_manager.get_learner_profile(submission.learner_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Learner not found")
    
    profile["pre_test_score"] = score
    profile["status"] = "ACTIVE"
    profile["mastery_level"] = score / 10.0 # Normalize 0-1
    
    # Save
    await state_manager.set(f"profile:{submission.learner_id}", profile)
    
    return {"status": "success", "score": score}
