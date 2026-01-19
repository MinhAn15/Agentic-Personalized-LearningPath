from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.models.schemas import KAGInput
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

_kag_agent = None

def set_kag_agent(agent):
    """Set KAG agent instance"""
    global _kag_agent
    _kag_agent = agent

@router.post("/analyze")
async def analyze_patterns(request: KAGInput) -> Dict[str, Any]:
    """
    Analyze aggregated learner patterns via KAG Agent (MemGPT).
    """
    try:
        if not _kag_agent:
            raise HTTPException(status_code=500, detail="KAG Agent not initialized")
        
        start_time = time.time()
        
        # Pass full payload + force_real flag
        result = await _kag_agent.execute(
            action=request.action,
            force_real=request.force_real,
            **request.payload
        )
        
        execution_time = (time.time() - start_time) * 1000  # ms
        
        if not result.get("success"):
            # Check if it's just a partial failure or critical
            if "error" in result:
                 logger.warning(f"KAG Execution warning: {result['error']}")
        
        result["execution_time_ms"] = execution_time
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_aggregated_statistics():
    """
    Get aggregated statistics across all learners.
    
    Returns overall mastery statistics, difficulty ratings, etc.
    """
    try:
        if not _kag_agent:
            raise HTTPException(status_code=500, detail="KAG Agent not initialized")
        
        # In production, would retrieve from cache/database
        return {
            "total_learners": 0,
            "total_concepts": 0,
            "average_success_rate": 0.0,
            "difficult_concepts": [],
            "easy_concepts": []
        }
    
    except Exception as e:
        logger.error(f"Statistics endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
