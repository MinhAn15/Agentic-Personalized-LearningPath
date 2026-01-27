from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging
import random

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
    cohort: str  # "pilot_treatment" or "pilot_control"
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
    req: Request, # For IP address
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
    # Using specific group names from schema
    cohort_group = "pilot_treatment" if random.random() < 0.5 else "pilot_control"
    
    profile = {
        "learner_id": learner_id,
        "name": request.name,
        "email": request.email,
        "age": request.age,
        "background": request.background,
        "cohort": cohort_group,
        "created_at": datetime.now().isoformat(),
        "status": "ONBOARDING"
    }
    
    try:
        # 1. Create Learner Record
        if hasattr(state_manager.postgres, "create_learner"):
            # Fix: Pass learner_id and profile
            await state_manager.postgres.create_learner(learner_id, profile)
        
        # 2. Record Consent (Audit Log)
        if hasattr(state_manager.postgres, "record_consent"):
            client_ip = req.client.host if req.client else "unknown"
            user_agent = req.headers.get("user-agent", "unknown")
            await state_manager.postgres.record_consent(
                learner_id, "v1.0", request.consent_agreed, client_ip, user_agent
            )
            
        # 3. Assign Experiment Group
        if hasattr(state_manager.postgres, "assign_experiment_group"):
            await state_manager.postgres.assign_experiment_group(learner_id, cohort_group)
            
        # 4. Cache profile
        await state_manager.set(f"profile:{learner_id}", profile)
        
        logger.info(f"Learner {learner_id} signed up. Cohort: {cohort_group}")
        
    except Exception as e:
        logger.error(f"Signup failed: {e}")
        # In production, we might want to rollback here
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")
    
    return LearnerProfileResponse(
        learner_id=learner_id,
        name=request.name,
        cohort=cohort_group,
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
