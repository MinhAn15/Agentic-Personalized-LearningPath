from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

_kag_agent = None

def set_kag_agent(agent):
    """Set KAG agent instance"""
    global _kag_agent
    _kag_agent = agent

class AnalysisRequest(BaseModel):
    """Request to analyze system-wide patterns"""
    analysis_depth: Optional[str] = "shallow"  # "shallow" or "deep"
    min_learners: Optional[int] = 10

@router.post("/analyze")
async def analyze_patterns(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Analyze aggregated learner patterns.
    
    This endpoint:
    1. Retrieves all learner Personal KGs
    2. Merges into aggregated view
    3. Calculates statistics
    4. Identifies patterns (difficult concepts, misconceptions)
    5. Generates course recommendations
    6. Predicts intervention points
    
    Example request:
    {
        "analysis_depth": "deep",
        "min_learners": 10
    }
    
    Example response:
    {
        "success": true,
        "num_learners_analyzed": 100,
        "statistics": {
            "SQL_WHERE": {"avg_mastery": 0.72, "struggle_rate": 0.24},
            "SQL_JOIN": {"avg_mastery": 0.35, "struggle_rate": 0.65}
        },
        "patterns": {...},
        "insights": [
            "⚠️ SQL_JOIN: Only 35% mastery, 65% struggle",
            "60% of JOIN failures had weak WHERE foundation"
        ],
        "recommendations": [
            "📚 Strengthen SQL_WHERE prerequisites",
            "📝 Create WHERE vs JOIN comparison",
            "🎯 Add SQL_WHERE practice exercises"
        ],
        "predictions": [
            "🚀 Next cohort: Allocate 2x time for SQL_WHERE",
            "🚩 Flag learners struggling with SQL_WHERE early"
        ]
    }
    """
    try:
        if not _kag_agent:
            raise HTTPException(status_code=500, detail="KAG Agent not initialized")
        
        start_time = time.time()
        
        result = await _kag_agent.execute(
            analysis_depth=request.analysis_depth,
            min_learners=request.min_learners
        )
        
        execution_time = (time.time() - start_time) * 1000  # ms
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
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
