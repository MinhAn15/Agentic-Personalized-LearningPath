from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime
import random # Mock data for now, replace with DB queries later

from backend.core.state_manager import CentralStateManager
from backend.database.database_factory import get_factory

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

# --- Dependencies ---
async def get_state_manager():
    factory = get_factory()
    return CentralStateManager(factory.redis, factory.postgres)

# --- Routes ---

@router.get("/stats/learners")
async def get_learner_roster(
    state_manager: CentralStateManager = Depends(get_state_manager)
):
    """
    Get list of all learners and their current status.
    """
    # In production: await state_manager.postgres.get_all_learners()
    # Mocking for Phase 3 scaffolding
    return {
        "total_learners": 25,
        "learners": [
            {
                "id": f"learner_{i}",
                "name": f"Student {i}",
                "cohort": "TREATMENT" if i % 2 == 0 else "CONTROL",
                "progress": random.randint(10, 90),
                "last_active": datetime.now().isoformat(),
                "status": "ACTIVE" if random.random() > 0.1 else "INACTIVE"
            }
            for i in range(25)
        ]
    }

@router.get("/stats/cohort-comparison")
async def get_cohort_stats(
    state_manager: CentralStateManager = Depends(get_state_manager)
):
    """
    Compare Treatment vs Control performance (Real-time).
    """
    # Mocking real-time aggregation
    return {
        "treatment": {
            "count": 13,
            "avg_mastery": 0.78,
            "avg_time_spent_mins": 145,
            "completion_rate": 0.45
        },
        "control": {
            "count": 12,
            "avg_mastery": 0.55,
            "avg_time_spent_mins": 130,
            "completion_rate": 0.20
        },
        "stat_significance": {
            "p_value": 0.04,
            "cohens_d": 0.85
        }
    }

@router.get("/stats/agent-health")
async def get_agent_health(
    state_manager: CentralStateManager = Depends(get_state_manager)
):
    """
    Monitor Agent performance and error rates.
    """
    return {
        "status": "HEALTHY",
        "agents": {
            "agent_1_knowledge": {"status": "UP", "latency_ms": 120, "errors_24h": 0},
            "agent_2_profiler": {"status": "UP", "latency_ms": 45, "errors_24h": 2},
            "agent_3_planner": {"status": "UP", "latency_ms": 350, "errors_24h": 0},
            "agent_4_tutor": {"status": "UP", "latency_ms": 1200, "errors_24h": 5},
            "agent_5_evaluator": {"status": "UP", "latency_ms": 800, "errors_24h": 1},
            "agent_6_kag": {"status": "UP", "latency_ms": 150, "errors_24h": 0},
        },
        "system_load": "LOW"
    }
