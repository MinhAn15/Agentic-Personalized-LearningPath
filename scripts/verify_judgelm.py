import asyncio
import logging
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Fix Path to include backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.evaluator_agent import EvaluatorAgent
from backend.core.event_bus import EventBus
from backend.models.evaluation import ErrorType

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("JudgeLM_Test")

# Mock Classes
class MockStateManager:
    def __init__(self):
        self.neo4j = MagicMock()
        self.neo4j.run_query = AsyncMock(return_value=[])
        self.redis = MagicMock()
    
    async def get_learner_profile(self, learner_id):
        return {}

    async def get_state(self, key):
        return None
    
    async def set_state(self, key, value):
        pass

class MockEventBus:
    def publish(self, channel, message):
        pass
    def subscribe(self, channel, callback):
        pass

class MockLLM:
    def __init__(self):
        self.acomplete = AsyncMock()

async def verify_judgelm():
    logger.info("🧪 Starting JudgeLM Verification...")
    
    # Setup Mocks
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    llm = MockLLM()
    
    # Patch Settings to avoid LlamaIndex validation
    with patch('backend.agents.evaluator_agent.get_settings'), \
         patch('backend.agents.evaluator_agent.Gemini'), \
         patch('backend.agents.evaluator_agent.SemanticScorer'), \
         patch('backend.agents.evaluator_agent.ErrorClassifier'), \
         patch('backend.agents.evaluator_agent.MasteryTracker'):
         
        agent = EvaluatorAgent("evaluator_test", state_manager, event_bus, llm=llm)
        
        # Test Case 1: Perfect Match (High Score)
        logger.info("\n🧪 Test 1: Perfect Match (Reference-Based)")
        
        # Mock LLM Response for JudgeLM
        valid_json_high = """
        {
            "justification_trace": "The student response perfectly matches the reference. Both identify that INNER JOIN returns only matching rows.",
            "score": 10.0,
            "dimensions": {
                "correctness": 10,
                "completeness": 10,
                "clarity": 10
            }
        }
        """
        llm.acomplete.return_value = MagicMock(text=valid_json_high)
        
        result_high = await agent._score_response(
            learner_response="INNER JOIN returns only rows that match in both tables.",
            expected_answer="INNER JOIN returns only rows that match in both tables.",
            explanation="It filters out non-matching rows.",
            target_bloom_level=2
        )
        
        logger.info(f"Score: {result_high['score']}")
        assert result_high["score"] == 1.0, f"Expected 1.0, got {result_high['score']}"
        logger.info("✅ High score verification passed.")

        # Test Case 2: Partial Match (Mid Score)
        logger.info("\n🧪 Test 2: Partial Match")
        
        valid_json_mid = """
        {
            "justification_trace": "The student is partially correct but misses the key detail about non-matching rows.",
            "score": 6.0,
            "dimensions": {
                "correctness": 6,
                "completeness": 5,
                "clarity": 8
            }
        }
        """
        llm.acomplete.return_value = MagicMock(text=valid_json_mid)
        
        result_mid = await agent._score_response(
            learner_response="It joins tables.",
            expected_answer="INNER JOIN returns only rows that match in both tables.",
            explanation="It filters out non-matching rows.",
            target_bloom_level=2
        )
        
        logger.info(f"Score: {result_mid['score']}")
        assert result_mid["score"] == 0.6, f"Expected 0.6, got {result_mid['score']}"
        logger.info("✅ Generalization logic verification passed (0.6).")

        # Test Case 3: JSON Parse Failure (Robustness)
        logger.info("\n🧪 Test 3: Malformed JSON Fallback")
        llm.acomplete.return_value = MagicMock(text="I give this a score of 5/10 but forgot JSON.")
        
        result_fail = await agent._score_response(
            learner_response="Bad format",
            expected_answer="Structure",
            explanation="...",
            target_bloom_level=2
        )
        
        logger.info(f"Score: {result_fail['score']}")
        assert result_fail["success"] == False, "Expected success=False for malformed JSON"
        assert result_fail["score"] == 0.0, "Expected 0.0 fallback"
        logger.info("✅ Robustness verification passed.")

    logger.info("\n🎉 All JudgeLM tests passed!")

if __name__ == "__main__":
    try:
        asyncio.run(verify_judgelm())
    except Exception as e:
        logger.error(f"Test Failed: {e}")
        exit(1)
