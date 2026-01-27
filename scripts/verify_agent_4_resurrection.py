import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import MagicMock, AsyncMock, patch
from backend.agents.tutor_agent import TutorAgent
from backend.models.dialogue import DialogueState, DialoguePhase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TutorVerification")

async def verify_resurrection():
    print("🚀 Starting Agent 4 Resurrection Verification...")
    
    # 1. Mock Dependencies
    mock_state_manager = MagicMock()
    mock_event_bus = MagicMock()
    mock_llm = AsyncMock()
    
    # Mock Neo4j to return valid context (Proof of Life for KAG)
    mock_neo4j = AsyncMock()
    mock_state_manager.neo4j = mock_neo4j
    
    # Mock run_query results
    async def mock_run_query(query, **kwargs):
        if "c:CourseConcept" in query and "l:Learner" not in query:
            # Course KG Retrieve (Projected Fields)
            print(f"   ✅ [Neo4j] Intercepted Course KG Query")
            return [{
                "name": "MockConcept", 
                "definition": "Integration is the reverse of differentiation.", 
                "examples": ["Area under curve"], 
                "misconceptions": ["Forgetting +C"],
                "prerequisites": ["Derivatives"],
                "subconcepts": []
            }]
        elif "l:Learner" in query:
             # Personal KG Retrieve
             print(f"   ✅ [Neo4j] Intercepted Personal KG Query")
             return [{
                 "learning_style": "VISUAL",
                 "mastery_level": 0.5,
                 "past_errors": ["Chain Rule Error"],
                 "personal_notes": ["Hard topic"]
             }]
        return []

    mock_neo4j.run_query.side_effect = mock_run_query
    
    # 2. Mock LLM correctly using llama_index MockLLM to pass isinstance checks
    from llama_index.core.llms import MockLLM
    from llama_index.core.base.llms.types import CompletionResponse
    
    class CapturingMockLLM(MockLLM):
        def __init__(self):
            super().__init__()
            
        async def acomplete(self, prompt: str, **kwargs):
            print("\n📝 [LLM Prompt Capture]:")
            print("-" * 40)
            
            # Check for Critical Fixes
            if "### CONTEXT FROM KNOWLEDGE GRAPH" in prompt and "Integration is the reverse of differentiation" in prompt:
                print("   ✅ FOUND: Context Injection (KAG)")
            else:
                print("   ❌ MISSING: Context Injection")
                
            if "Scaffolding Strategy: DETAILED BREAKDOWN" in prompt:
                 print("   ✅ FOUND: Hint Level 3 Strategy (Scaffolding)")
            else:
                 print("   ❌ MISSING: Hint Level 3 Strategy")
            print("-" * 40)
            
            return CompletionResponse(text="CoT: Integration is finding the area. Student Hint: Start by visualizing the area under the curve.")

    mock_llm = CapturingMockLLM()

    # 2. Initialize Agent
    agent = TutorAgent("tutor-001", mock_state_manager, mock_event_bus, llm=mock_llm)
    # Bypass settings to avoid mock mode check skipping logic
    agent.settings = MagicMock()
    agent.settings.MOCK_LLM = False 
    
    # 3. Execute with Hint Level 3
    print("\n⚡ Executing Tutor with hint_level=3...")
    
    # Force phase to QUESTIONING to test CoT + Hint Logic
    mock_state = DialogueState(learner_id="test_user", concept_id="test_concept")
    mock_state.phase = DialoguePhase.QUESTIONING
    mock_state.concept_id = "test_concept"
    
    # Patch _get_or_create_dialogue_state to return our state
    with patch.object(agent, '_get_or_create_dialogue_state', return_value=mock_state):
        # Create input object
        class TutorInput:
            learner_id = "test_user"
            question = "Help me understand integration"
            concept_id = "test_concept"
            force_real = True
            hint_level = 3
            
        result = await agent.execute(tutor_input=TutorInput())
    
    print("\n📊 Verification Finished.")

if __name__ == "__main__":
    asyncio.run(verify_resurrection())
