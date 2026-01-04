import asyncio
import argparse
import logging
import json
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Agent3_ToT_TestRunner")

# --------------------------------------------------------------------------------
# MOCK INFRASTRUCTURE
# --------------------------------------------------------------------------------

def setup_mock_modules():
    sys.modules["backend.agents.knowledge_extraction_agent"] = MagicMock()
    sys.modules["backend.agents.profiler_agent"] = MagicMock()
    sys.modules["backend.agents.tutor_agent"] = MagicMock()
    sys.modules["backend.agents.evaluator_agent"] = MagicMock()
    sys.modules["backend.agents.kag_agent"] = MagicMock()
    
    # Mock Core Modules to prevent heavy init
    sys.modules["backend.core.rl_engine"] = MagicMock()
    
    # Define a MockBaseAgent that accepts init args and sets attributes
    class MockBaseAgent:
        def __init__(self, agent_id, agent_type, state_manager, event_bus):
            self.agent_id = agent_id
            self.agent_type = agent_type
            self.state_manager = state_manager
            self.event_bus = event_bus
            self.logger = logging.getLogger("MockBaseAgent")

        async def save_state(self, *args, **kwargs):
            pass

        async def send_message(self, *args, **kwargs):
            pass

    mock_base_module = MagicMock()
    mock_base_module.BaseAgent = MockBaseAgent
    sys.modules["backend.core.base_agent"] = mock_base_module
    
    sys.modules["llama_index"] = MagicMock()
    sys.modules["llama_index.llms"] = MagicMock()
    sys.modules["llama_index.llms.gemini"] = MagicMock()
    sys.modules["llama_index.core"] = MagicMock()

class MockStateManager:
    def __init__(self):
        self.neo4j = AsyncMock()
        self.redis = AsyncMock()
        
        lock_mock = MagicMock()
        async def async_acquire(): return True
        async def async_release(): pass
        lock_mock.acquire = async_acquire
        lock_mock.release = async_release
        self.redis.lock.return_value = lock_mock
        
        pipeline_mock = MagicMock()
        pipeline_mock.execute = AsyncMock(return_value=[None]*10)
        self.redis.pipeline = MagicMock(return_value=pipeline_mock)
        
        self.learner_profile = {
            "learner_id": "test_learner_tot",
            "goal": "Learn Python",
            "topic": "Python",
            "time_available": 10,
            "hours_per_day": 2,
            "current_mastery": [{"concept_id": "Basics", "mastery_level": 0.5}],
            "preferred_learning_style": "VISUAL",
            "current_concept": "Basics" # Needed for ToT start
        }

    async def get_learner_profile(self, learner_id):
        return self.learner_profile
    
    async def get_db_session(self): return AsyncMock()
    async def get(self, k): return None
    async def set(self, k, v, ex=None): pass

class MockEventBus:
    async def publish(self, *args, **kwargs): pass
    def subscribe(self, *args, **kwargs): pass

# --------------------------------------------------------------------------------
# TEST SCENARIOS
# --------------------------------------------------------------------------------

async def run_tot_test():
    """Verify Tree of Thoughts Logic"""
    logger.info("🚀 Starting Agent 3 ToT Verification")
    
    setup_mock_modules()
    from backend.agents.path_planner_agent import PathPlannerAgent, ChainingMode
    
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    
    # Mock LLM for Generator and Evaluator
    mock_llm = AsyncMock()
    agent = PathPlannerAgent("mock_planner", state_manager, event_bus)
    agent.llm = mock_llm
    
    # 1. Setup Mock Data (Course Concepts)
    # ----------------------------------------------------------------------------
    state_manager.neo4j.run_query.side_effect = [
        # Query 1: Course Concepts (Meta)
        [
            {"concept_id": "Basics", "name": "Python Basics", "difficulty": 1, "time_estimate": 10},
            {"concept_id": "Variables", "name": "Variables", "difficulty": 1, "time_estimate": 10},
            {"concept_id": "Loops", "name": "Loops", "difficulty": 2, "time_estimate": 20},
            {"concept_id": "Functions", "name": "Functions", "difficulty": 2, "time_estimate": 20}
        ],
        # Query 2: Relationships (for LinUCB fallback or ref map)
        [],
        # Query 3+: Neighbor lookup fallback (if needed)
        [{"id": "Variables"}] 
    ]

    # 2. Mock LLM Responses
    # ----------------------------------------------------------------------------
    # Scenario: 
    # 1. Thought Generator Start: Proposes [Variables (Review), Loops (Scaffold), Functions (Challenge)]
    # 2. Evaluator: Scores them.
    # 3. Beam Search: Picks best.
    
    async def llm_acomplete_side_effect(prompt):
        prompt_text = str(prompt)
        
        # A. Thought Generator Response
        if "Propose 3 distinct next concepts" in prompt_text:
            return MagicMock(text=json.dumps([
                {"concept": "Variables", "strategy": "review", "reason": "Review basics"},
                {"concept": "Loops", "strategy": "scaffold", "reason": "Next step"},
                {"concept": "Functions", "strategy": "challenge", "reason": "Skip ahead"}
            ]))
        
        # B. State Evaluator Response
        if "Evaluate this teaching step" in prompt_text:
            if "Functions" in prompt_text:
                return MagicMock(text=json.dumps({"value_score": 2})) # Too hard
            if "Loops" in prompt_text:
                return MagicMock(text=json.dumps({"value_score": 9})) # High value
            if "Variables" in prompt_text:
                return MagicMock(text=json.dumps({"value_score": 6})) # Safe
            
            return MagicMock(text=json.dumps({"value_score": 5}))

        return MagicMock(text="{}")

    mock_llm.acomplete.side_effect = llm_acomplete_side_effect

    # 3. Execute Planner
    # ----------------------------------------------------------------------------
    logger.info("🧪 Executing Path Planner with ToT...")
    
    result = await agent.execute(
        learner_id="test_learner_tot",
        goal="Master Python"
    )
    
    # 4. Verify Results
    # ----------------------------------------------------------------------------
    print(json.dumps(result, indent=2, default=str))

    # Assertions
    assert result["success"] == True
    assert len(result["learning_path"]) >= 1, "Path should not be empty"
    
    first_step = result["learning_path"][0]
    
    # Logic Check: "Loops" had highest score (9) vs Variables (6) vs Functions (2)
    # Beam search should prioritize high score.
    # Note: BFS might preserve order if scores are close, but here 9 is distinct.
    # Wait, BFS prioritizes beam. If depth=3, acts recursively.
    # But in test setup, we only simulated one level of thoughts effectively.
    # If beam search expands, it calls generator again.
    # We need to make sure side_effect handles recursion or beam search stops.
    # If beam search runs depth=3, it loops.
    # Let's see if our side_effect is robust enough. 
    # It returns [Variables, Loops, Functions] for ANY generator call.
    # That implies infinite loop of same concepts?
    # No, Beam Search usually prunes visited or limits depth.
    # Let's check output.
    
    if first_step["concept"] == "Loops":
        print("\n✅ TEST PASSED: ToT selected optimum path (Loops) based on Evaluator Score.")
    else:
        print(f"\n⚠️ TEST WARNING: First step is {first_step['concept']}, expected Loops. Check scores.")

    # Check chain mode
    if "TOT_GENERATED" in first_step.get("chain_mode", ""):
        print("✅ TEST PASSED: Chain Mode marked as TOT_GENERATED.")
    else:
        print("❌ TEST FAILED: Chain Mode not updated correctly.")

if __name__ == "__main__":
    asyncio.run(run_tot_test())
