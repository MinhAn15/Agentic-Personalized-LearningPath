import asyncio
import logging
import argparse
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

# Adjust path to include project root
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock llama_index before importing agent
# Mock llama_index before importing agent
# Mock llama_index before importing agent
sys.modules['llama_index'] = MagicMock()
sys.modules['llama_index.llms'] = MagicMock()
sys.modules['llama_index.core'] = MagicMock()

# 1. Mock 'llama_index.core.base' hierarchy to support llm_factory imports
mock_base = MagicMock()
sys.modules['llama_index.core.base'] = mock_base
sys.modules['llama_index.core.base.llms'] = MagicMock()
sys.modules['llama_index.core.base.llms.types'] = MagicMock()

# 2. Mock specific classes imported from types
mock_types = sys.modules['llama_index.core.base.llms.types']
mock_types.ChatMessage = MagicMock
mock_types.MessageRole = MagicMock

# 3. Ensure other submodules are available
sys.modules['llama_index.core.llms'] = MagicMock()
sys.modules['llama_index.core.embeddings'] = MagicMock()
sys.modules['llama_index.embeddings'] = MagicMock()
sys.modules['llama_index.llms.gemini'] = MagicMock()
sys.modules['llama_index.embeddings.gemini'] = MagicMock()

from backend.agents.evaluator_agent import EvaluatorAgent, ErrorType, PathDecision
from backend.core.constants import (
    THRESHOLD_MASTERED, THRESHOLD_PROCEED
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Agent5_TestRunner")

# Mock State Manager
class MockStateManager:
    def __init__(self):
        self.redis = MagicMock()
        self.neo4j = AsyncMock()
        self.neo4j.run_query = AsyncMock(return_value=[]) # Default empty
    
    async def get_learner_profile(self, learner_id):
        return {"current_mastery": [], "concept_attempts": {}}

    async def get_db_session(self):
        return AsyncMock()

    async def get(self, key):
        return None

    async def set(self, key, value, ttl=None):
        pass

# Mock Event Bus
class MockEventBus:
    async def publish(self, message_type, payload, sender=None, receiver=None):
        logger.info(f"EventBus published: {message_type} -> {receiver} (from {sender}) - {payload}")
    
    def subscribe(self, event_type, callback):
        logger.info(f"EventBus subscribed to: {event_type}")

    async def send_message(self, receiver, message_type, payload):
        logger.info(f"Sending message: {message_type} -> {receiver}")

# Mock LLM
class MockLLM:
    async def acomplete(self, prompt: str):
        # Determine behavior based on prompt content
        prompt_lower = prompt.lower()
        
        if "score this learner response" in prompt_lower or "[judge]" in prompt_lower or "checking the quality of the answer" in prompt_lower:
            # Logic for scoring
            if "where combines" in prompt_lower: return MagicMock(text='10.0 2.0\nExplanation: Wrong.\n```json\n{"correctness": 2, "completeness": 2, "clarity": 5}\n```')
            if "where filters" in prompt_lower: return MagicMock(text='10.0 10.0\nExplanation: Perfect.\n```json\n{"correctness": 10, "completeness": 10, "clarity": 10}\n```')
            if "almost right" in prompt_lower: return MagicMock(text='10.0 7.0\nExplanation: Good.\n```json\n{"correctness": 8, "completeness": 6, "clarity": 8}\n```')
            # Fallback
            return MagicMock(text='10.0 5.0\nExplanation: Okay.\n```json\n{"correctness": 5, "completeness": 5, "clarity": 5}\n```')
            
        if "classify this error" in prompt_lower:
            if "where combines" in prompt_lower: return MagicMock(text='CONCEPTUAL')
            return MagicMock(text='CARELESS')
            
        if "what misconception" in prompt_lower:
            return MagicMock(text='Confuses WHERE and JOIN')
            
        if "generate personalized feedback" in prompt_lower:
            return MagicMock(text='Feedback: You seem to be confusing concepts.')
            
        return MagicMock(text='{"score": 0.0}')

# ------------------------------------------------------------------------
# MOCK MODE
# ------------------------------------------------------------------------
async def run_mock_mode():
    logger.info("🚀 Starting Agent 5 Mock Test")
    
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    llm = MockLLM()
    
    agent = EvaluatorAgent("mock_evaluator", state_manager, event_bus, llm=llm)
    
    # IMPORTANT: Disable the agent's internal "lazy mock" short-circuit
    # so it actually calls our sophisticated MockLLM logic.
    agent.settings.MOCK_LLM = False
    
    # Mock Neo4j Concept Retrieval
    state_manager.neo4j.run_query = AsyncMock(return_value=[{
        "c": {
            "concept_id": "SQL_WHERE", "name": "WHERE Clause", 
            "difficulty": 2, "common_misconceptions": ["Confuses WHERE with JOIN"]
        },
        "misconceptions": ["Confuses WHERE with JOIN"],
        "prerequisites": []
    }])

    # 1. Test Scoring Logic (High Score)
    logger.info("\n🧪 Testing Correct Response...")
    res_correct = await agent.execute(
        learner_id="learner1",
        concept_id="SQL_WHERE",
        learner_response="WHERE filters rows based on condition",
        expected_answer="WHERE filters rows",
    )
    logger.info(f"Score: {res_correct['score']} (Expected: 1.0)")
    assert res_correct['score'] >= 0.9
    logger.info(f"Decision: {res_correct['decision']} (Expected: MASTERED)")
    assert res_correct['decision'] == PathDecision.MASTERED.value

    # 2. Test Error Logic (Conceptual Error)
    logger.info("\n🧪 Testing Conceptual Error...")
    res_wrong = await agent.execute(
        learner_id="learner1",
        concept_id="SQL_WHERE",
        learner_response="WHERE combines two tables together", # Wrong
        expected_answer="WHERE filters rows",
    )
    logger.info(f"Score: {res_wrong['score']} (Expected: ~0.2)")
    assert res_wrong['score'] < 0.3
    logger.info(f"Error: {res_wrong['error_type']} (Expected: CONCEPTUAL)")
    assert res_wrong['error_type'] == ErrorType.CONCEPTUAL.value
    logger.info(f"Decision: {res_wrong['decision']} (Expected: REMEDIATE)")
    assert res_wrong['decision'] == PathDecision.REMEDIATE.value

    # 3. Test 5-Path Decision Boundaries
    logger.info("\n🧪 Testing Decision Boundaries...")
    
    # Case: Proceed (0.8)
    # Mock specific score injection via private method for direct boundary test
    decision = await agent._make_path_decision(
        score=0.85, current_mastery=0.0, error_type=ErrorType.CORRECT, concept_difficulty=2
    )
    logger.info(f"Score 0.85 -> {decision} (Expected: PROCEED)")
    assert decision == PathDecision.PROCEED
    
    # Case: Alternate (0.65)
    decision = await agent._make_path_decision(
        score=0.65, current_mastery=0.0, error_type=ErrorType.INCOMPLETE, concept_difficulty=2
    )
    logger.info(f"Score 0.65 -> {decision} (Expected: ALTERNATE)")
    assert decision == PathDecision.ALTERNATE

    logger.info("\n✅ MOCK TEST PASSED")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['mock', 'real'], default='mock')
    args = parser.parse_args()
    
    if args.mode == 'mock':
        asyncio.run(run_mock_mode())
    else:
        logger.warning("Real mode not fully configured for unit test run.")
