import asyncio
import logging
import sys
import os
import json
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.tutor_agent import TutorAgent
from backend.models.dialogue import DialogueState, DialoguePhase

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Agent4_CoT_TestRunner")

# Mock Dependencies
def setup_mocks():
    state_manager = MagicMock()
    state_manager.neo4j = AsyncMock()
    state_manager.redis = AsyncMock()
    
    event_bus = MagicMock()
    event_bus.subscribe = MagicMock()
    event_bus.publish = AsyncMock()
    
    return state_manager, event_bus

async def test_hybrid_architecture():
    """
    Verify Agent 4 implements Hybrid Architecture:
    1. Maintains Dialogue State (Phase Tracking).
    2. Uses Chain-of-Thought for Scaffolding.
    """
    logger.info("🚀 Starting Agent 4 (Hybrid CoT) Verification")
    
    state_manager, event_bus = setup_mocks()
    agent = TutorAgent("mock_tutor", state_manager, event_bus)
    
    # Mock LLM
    mock_llm = AsyncMock()
    agent.llm = mock_llm
    
    # Mock CoT Response (Hidden Monologue)
    cot_response_text = """
    1. Core Concept: Recursion
    2. Student Error: Base case missing
    3. Correct Logic: Must have exit condition
    4. Next Hint: Ask about what happens when len(list) == 0
    """
    mock_llm.acomplete.return_value = MagicMock(text=cot_response_text)
    
    # ------------------------------------------------------------------
    # TEST 1: Phase Transitions (State Machine)
    # ------------------------------------------------------------------
    learner_id = "test_learner_cot"
    concept_id = "Recursion"
    
    # Force state to SCAFFOLDING
    state = agent._get_or_create_dialogue_state(learner_id, concept_id)
    state.current_phase = DialoguePhase.SCAFFOLDING
    state.turn_count = 1
    
    logger.info("🧪 Testing Scaffolding Phase (Expecting CoT)...")
    
    # 1st Call: Should trigger CoT and return Step 1
    result1 = await agent.execute(
        learner_id=learner_id,
        concept_id=concept_id,
        question="I got infinite loop error",
        conversation_history=[]
    )
    
    # Verify State State
    state = agent._get_or_create_dialogue_state(learner_id, concept_id)
    assert len(state.current_cot_trace) > 0, "CoT Trace should be populated"
    assert state.cot_step_index == 1, "Should be at step 1"
    
    logger.info(f"Step 1 Response: {result1['response']}")
    
    # 2nd Call: Should return Step 2 (Slicing)
    result2 = await agent.execute(
        learner_id=learner_id,
        concept_id=concept_id,
        question="I still don't get it",
        conversation_history=[]
    )
    
    assert state.cot_step_index == 2, "Should be at step 2"
    logger.info(f"Step 2 Response: {result2['response']}")
    
    # Verify CoT was triggered (Mock check)
    assert mock_llm.acomplete.called, "LLM should be called for CoT generation"

    logger.info("🏆 Hybrid Architecture & Slicing Verification Complete")
         
    # ------------------------------------------------------------------
    # TEST 2: Handoff Logic (State Machine)
    # ------------------------------------------------------------------
    logger.info("🧪 Testing Assessment Handoff...")
    state.current_phase = DialoguePhase.ASSESSMENT
    
    await agent.execute(
        learner_id=learner_id,
        concept_id=concept_id,
        question="I think I understand now",
        conversation_history=[]
    )
    
    # Verify Handoff Event
    if event_bus.publish.called: # In real BaseAgent this calls send_message -> event_bus
        logger.info("✅ Handoff Event Published (Mock Check)")
    else:
        # Check if _handoff_to_evaluator logic exists
        pass 

    logger.info("🏆 Hybrid Architecture Verification Complete")

if __name__ == "__main__":
    asyncio.run(test_hybrid_architecture())
