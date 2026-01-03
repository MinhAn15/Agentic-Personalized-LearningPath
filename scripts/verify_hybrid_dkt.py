import asyncio
import os
import sys
import logging
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Evaluator_HybridDKT_Test")

# ==========================================
# HOTFIX: MOCK SIBLING AGENTS
# ==========================================
sys.modules["backend.agents.knowledge_extraction_agent"] = MagicMock()
sys.modules["backend.agents.path_planner_agent"] = MagicMock()
sys.modules["backend.agents.tutor_agent"] = MagicMock()
sys.modules["backend.agents.profiler_agent"] = MagicMock()
sys.modules["backend.agents.kag_agent"] = MagicMock()
sys.modules["backend.services.instructor_notification"] = MagicMock()

# Mock LlamaIndex
sys.modules["llama_index.llms.gemini"] = MagicMock()

# Mock Constants to avoid import error if config missing
sys.modules["backend.core.constants"] = MagicMock()
sys.modules["backend.config"] = MagicMock()

class MockStateManager:
    def __init__(self):
        self.neo4j = AsyncMock()
        self.redis = AsyncMock()
        self.postgres = AsyncMock()
        self.neo4j.run_query.return_value = []
        
    async def get_learner_profile(self, learner_id):
        return {"current_mastery": []}

    async def save_state(self, key, value):
        logger.info(f"💾 Saving State: {key} -> {value}")
        return True

    async def set(self, key, value, ttl=None):
        logger.info(f"💾 Mock Set: {key} -> {value}")
        return True

async def verify_hybrid_dkt():
    """Verify Hybrid DKT-LLM Logic in Evaluator Agent"""
    from backend.agents.evaluator_agent import EvaluatorAgent, ErrorType
    
    logger.info("\n🧪 1. Initializing Evaluator Agent (Mock Mode)...")
    state_manager = MockStateManager()
    event_bus = MagicMock()
    
    # Mock LLM response to simulate "Adjustment"
    mock_llm = MagicMock()
    mock_llm.acomplete = AsyncMock()
    
    agent = EvaluatorAgent(
        agent_id="eval_test",
        state_manager=state_manager,
        event_bus=event_bus,
        llm=mock_llm
    )
    
    # ====================================================
    # TEST CASE 1: COLD START (No History)
    # ====================================================
    logger.info("\n🧪 TEST CASE 1: COLD START (Difficulty=5/Hard)")
    # Expected Prior: 1.0 - (5 * 0.15) = 0.25
    # LLM simulates "Slightly positive adjustment" -> 0.35
    mock_llm.acomplete.return_value = MagicMock(text="0.35")
    
    new_mastery = await agent._update_learner_mastery(
        learner_id="learner_1",
        concept_id="concept_hard",
        score=0.9, # Correct
        current_mastery=0.0, # Cold start
        concept_difficulty=5,
        error_type=None
    )
    
    logger.info(f"Result 1: {new_mastery}")
    if 0.3 <= new_mastery <= 0.4:
        logger.info("✅ Cold Start Logic Verified (Hard Concept -> Low Prior -> LLM Adjusted)")
    else:
        logger.error(f"❌ Cold Start Logic Failed. Got {new_mastery}, expected ~0.35")

    # ====================================================
    # TEST CASE 2: HYBRID ADJUSTMENT (History Exists)
    # ====================================================
    logger.info("\n🧪 TEST CASE 2: HYBRID ADJUSTMENT (Previous=0.8, Incorrect Response)")
    # Scenario: Student had 0.8, but verifies incorrectly with CONCEPTUAL error.
    # LLM should drop significantly (e.g., to 0.4)
    mock_llm.acomplete.return_value = MagicMock(text="0.40")
    
    new_mastery = await agent._update_learner_mastery(
        learner_id="learner_1",
        concept_id="concept_med",
        score=0.2, # Incorrect
        current_mastery=0.8, # Was high
        concept_difficulty=3,
        error_type=ErrorType.CONCEPTUAL,
        misconception="Confuses JOIN with UNION"
    )
    
    logger.info(f"Result 2: {new_mastery}")
    if new_mastery == 0.4:
        logger.info("✅ Hybrid Adjustment Verified (Conceptual Error -> Significant Drop)")
    else:
        logger.error(f"❌ Hybrid Logic Failed. Got {new_mastery}, expected 0.4")

    # ====================================================
    # TEST CASE 3: LLM FALLBACK (Invalid Output)
    # ====================================================
    logger.info("\n🧪 TEST CASE 3: LLM FALLBACK (Non-float output)")
    mock_llm.acomplete.return_value = MagicMock(text="I cannot determine mastery.")
    
    # Should use Step Size Fallback (e.g., current 0.5 + 0.1 = 0.6 for correct)
    new_mastery = await agent._update_learner_mastery(
        learner_id="learner_1",
        concept_id="concept_easy",
        score=0.9,
        current_mastery=0.5,
        concept_difficulty=2
    )
    
    logger.info(f"Result 3: {new_mastery}")
    if new_mastery == 0.6:
        logger.info("✅ Fallback Logic Verified (Legacy BKT Step Size used)")
    else:
        logger.error(f"❌ Fallback Logic Failed. Got {new_mastery}, expected 0.6")

if __name__ == "__main__":
    asyncio.run(verify_hybrid_dkt())
