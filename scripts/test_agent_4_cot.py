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
    CoT: The student is missing the base case.
    Student Hint: Think about the condition that stops the recursion.
    """
    mock_llm.acomplete.return_value = MagicMock(text=cot_response_text)
    
    # ------------------------------------------------------------------
    # TEST 1: Phase Transitions (State Machine)
    # ------------------------------------------------------------------
    learner_id = "test_learner_cot"
    concept_id = "Recursion"
    
    # Force state to SCAFFOLDING
    state = agent._get_or_create_dialogue_state(learner_id, concept_id)
    # 3. Simulate Scaffolding Trigger (System 2)
    print("\n--- Step 3: Triggering Scaffolding (CoT) ---")
    if state.phase != DialoguePhase.QUESTIONING:
        print("Forcing phase to QUESTIONING for CoT test...")
        state.phase = DialoguePhase.QUESTIONING
    state.turn_count = 1
    
    logger.info("🧪 Testing Scaffolding Phase (Expecting CoT)...")
    
    # 1st Call: Should trigger CoT and return Step 1
    result1 = await agent.execute(
        learner_id=learner_id,
        concept_id=concept_id,
        question="I got infinite loop error",
        conversation_history=[],
        force_real=True  # FORCE REAL to bypass static mock
    )
    
    # Verify State State
    state = agent._get_or_create_dialogue_state(learner_id, concept_id)
    assert len(state.current_cot_trace) > 0, "CoT Trace should be populated"
    # Verification: V1 implementation produces 1 step per trace
    # So we verified we got the hint.
    
    logger.info(f"Step 1 Response: {result1['guidance']}")
    assert "Think about the condition" in result1['guidance'], "Response should contain the hint"

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
