
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
sys.modules['llama_index'] = MagicMock()
sys.modules['llama_index.llms'] = MagicMock()
sys.modules['llama_index.llms.gemini'] = MagicMock()
sys.modules['llama_index.embeddings'] = MagicMock()
sys.modules['llama_index.embeddings.gemini'] = MagicMock()
sys.modules['llama_index.core'] = MagicMock()

from backend.agents.tutor_agent import TutorAgent, SocraticState
from backend.models.dialogue import UserIntent
from backend.core.base_agent import AgentType

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Agent4_TestRunner")

# Mock State Manager
class MockStateManager:
    def __init__(self):
        self.redis = MagicMock()
        self.neo4j = AsyncMock()
    
    async def get_db_session(self):
        return AsyncMock()

    async def get(self, key):
        return await self.redis.get(key)

    async def set(self, key, value, ttl=None):
        await self.redis.set(key, value, ttl)

# Mock Event Bus
class MockEventBus:
    async def publish(self, message_type, payload, sender=None, receiver=None):
        logger.info(f"EventBus published: {message_type} -> {receiver} (from {sender}) - {payload}")
    
    def subscribe(self, event_type, callback):
        logger.info(f"EventBus subscribed to: {event_type}")

# Mock LLM
class MockLLM:
    async def acomplete(self, prompt: str):
        # Return different responses based on prompt content
        if "Classify the learner's intent" in prompt:
            if "how to fix" in prompt.lower():
                return MagicMock(text="HELP_SEEKING")
            if "why" in prompt.lower():
                return MagicMock(text="SENSE_MAKING")
            return MagicMock(text="GENERAL")
        
        # Default Socratic response
        return MagicMock(text="This is a Socratic response. What do you think about X? ?")

# ------------------------------------------------------------------------
# MOCK MODE
# ------------------------------------------------------------------------
async def run_mock_mode():
    logger.info("🚀 Starting Agent 4 Mock Test")
    
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    llm = MockLLM()
    
    agent = TutorAgent("mock_tutor", state_manager, event_bus, llm=llm)
    
    # 1. Test Socratic State Determination
    logger.info("\n🧪 Testing Socratic State Determination...")
    
    # Scenario A: New learner, just probing
    state_a = agent._determine_socratic_state(
        hint_level=0, current_mastery=0.2, conversation_turns=0, intent=UserIntent.SENSE_MAKING
    )
    logger.info(f"Scenario A (Probing): {state_a} (Expected: PROBING)")
    assert state_a == SocraticState.PROBING
    
    # Scenario B: Stuck learner, needs help
    state_b = agent._determine_socratic_state(
        hint_level=0, current_mastery=0.2, conversation_turns=1, intent=UserIntent.HELP_SEEKING
    )
    logger.info(f"Scenario B (Help Seeking): {state_b} (Expected: SCAFFOLDING)")
    assert state_b == SocraticState.SCAFFOLDING
    
    # Scenario C: High mastery, Protege Effect
    with patch('random.random', return_value=0.1): # Force trigger
        state_c = agent._determine_socratic_state(
            hint_level=0, current_mastery=0.8, conversation_turns=3
        )
        logger.info(f"Scenario C (high mastery): {state_c} (Expected: TEACH_BACK)")
        assert state_c == SocraticState.TEACH_BACK

    # 2. Test 3-Layer Grounding (Mocked)
    logger.info("\n🧪 Testing 3-Layer Grounding...")
    
    # Mock Retrieve Methods
    agent._rag_retrieve = AsyncMock(return_value=({"chunks": ["text"]}, 0.8))
    agent._course_kg_retrieve = AsyncMock(return_value=({"definition": "A Loop is..."}, 0.9))
    agent._personal_kg_retrieve = AsyncMock(return_value=({"mastery": 0.5}, 0.5))
    agent._detect_conflict = AsyncMock(return_value=(False, 0.9)) # No conflict
    
    grounding = await agent._three_layer_grounding("What is a loop?", "Loops", "learner1")
    
    logger.info(f"Grounding Result: {grounding['confidence']:.2f}")
    
    # Verify weights: 0.8*0.4 + 0.9*0.35 + 0.5*0.25 = 0.32 + 0.315 + 0.125 = 0.76
    expected_score = 0.8 * agent.W_DOC + 0.9 * agent.W_KG + 0.5 * agent.W_PERSONAL
    assert abs(grounding['confidence'] - expected_score) < 0.01
    logger.info(f"✅ Confidence Score Correct: {grounding['confidence']:.3f}")

    # 3. Test Conflict Detection Logic
    logger.info("\n🧪 Testing Conflict Penalty...")
    agent._detect_conflict = AsyncMock(return_value=(True, 0.4)) # Conflict!
    grounding_conflict = await agent._three_layer_grounding("What is a loop?", "Loops", "learner1")
    
    # Reduced score should be old_score - PENALTY
    expected_conflict_score = expected_score - agent.CONFLICT_PENALTY
    
    logger.info(f"Conflict Score: {grounding_conflict['confidence']:.2f} (Expected ~{expected_conflict_score:.2f})")
    assert abs(grounding_conflict['confidence'] - expected_conflict_score) < 0.01
    logger.info("✅ Conflict Penalty Applied")

    logger.info("\n✅ MOCK TEST PASSED")

# ------------------------------------------------------------------------
# REAL MODE
# ------------------------------------------------------------------------
async def run_real_mode():
    logger.info("🚀 Starting Agent 4 Real Mode Test (Requires Neo4j/Redis)")
    from backend.services.central_state_manager import CentralStateManager
    from backend.services.event_bus import EventBus
    
    state_manager = CentralStateManager()
    await state_manager.connect()
    
    bus = EventBus()
    await bus.connect()
    
    agent = TutorAgent("real_tutor", state_manager, bus)
    
    input_data = {
        "learner_id": "test_learner_real",
        "question": "Why do I need functions?",
        "concept_id": "Functions",
        "conversation_history": []
    }
    
    logger.info(f"Input: {input_data}")
    result = await agent.execute(**input_data)
    
    logger.info(f"Result: {result}")
    
    if result["success"]:
        logger.info("✅ Real execution successful")
    else:
        logger.error(f"❌ Real execution failed: {result.get('error')}")

    await state_manager.close()
    await bus.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['mock', 'real'], default='mock')
    args = parser.parse_args()
    
    if args.mode == 'mock':
        asyncio.run(run_mock_mode())
    else:
        asyncio.run(run_real_mode())
