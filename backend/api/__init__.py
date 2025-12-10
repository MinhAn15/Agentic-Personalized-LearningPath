"""
API Routes for Agentic Learning Path System

This module contains all FastAPI routers for the agents.
"""

from fastapi import APIRouter

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Import and include sub-routers
from backend.api.learning_path import router as learning_path_router
from backend.api.profile import router as profile_router
from backend.api.assessment import router as assessment_router
from backend.api.tutor import router as tutor_router
from backend.api.artifacts import router as artifacts_router

api_router.include_router(learning_path_router, prefix="/learning-path", tags=["Learning Path"])
api_router.include_router(profile_router, prefix="/profile", tags=["Profile"])
api_router.include_router(assessment_router, prefix="/assessment", tags=["Assessment"])
api_router.include_router(tutor_router, prefix="/tutor", tags=["Tutor"])
api_router.include_router(artifacts_router, prefix="/artifacts", tags=["Artifacts"])

__all__ = ["api_router"]
