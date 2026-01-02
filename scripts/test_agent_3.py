import asyncio
import argparse
import logging
import json
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Agent3_TestRunner")

# --------------------------------------------------------------------------------
# MOCK INFRASTRUCTURE
# --------------------------------------------------------------------------------

def setup_mock_modules():
    """Mock external dependencies for isolated testing"""
    sys.modules["backend.agents.knowledge_extraction_agent"] = MagicMock()
    sys.modules["backend.agents.profiler_agent"] = MagicMock()
    sys.modules["backend.agents.tutor_agent"] = MagicMock()
    sys.modules["backend.agents.evaluator_agent"] = MagicMock()
    sys.modules["backend.agents.kag_agent"] = MagicMock()
    
    # Mock LlamaIndex
    sys.modules["llama_index"] = MagicMock()
    sys.modules["llama_index.llms"] = MagicMock()
    sys.modules["llama_index.llms.gemini"] = MagicMock()
    sys.modules["llama_index.core"] = MagicMock()

class MockStateManager:
    def __init__(self):
        self.neo4j = AsyncMock()
        self.redis = AsyncMock()
        
        # Mock Redis Lock
        lock_mock = MagicMock()
        async def async_acquire(): return True
        async def async_release(): pass
        lock_mock.acquire = async_acquire
        lock_mock.release = async_release
        self.redis.lock.return_value = lock_mock
        
        # Mock Redis Pipeline (Synchronous creation, Async execute)
        pipeline_mock = MagicMock()
        pipeline_mock.execute = AsyncMock(return_value=[None]*10) # Return empty results
        
        # KEY FIX: Overwrite the method to be synchronous MagicMock, not AsyncMock
        self.redis.pipeline = MagicMock(return_value=pipeline_mock)
        
        # Mock Learner Profile
        self.learner_profile = {
            "learner_id": "test_learner_123",
            "goal": "Learn Python",
            "topic": "Python",
            "time_available": 10,
            "hours_per_day": 2,
            "current_mastery": [
                {"concept_id": "Python_Basics", "mastery_level": 0.8}
            ],
            "preferred_learning_style": "VISUAL",
            "profile_vector": [0.1] * 10
        }

    async def get_learner_profile(self, learner_id):
        return self.learner_profile
    
    async def get_db_session(self):
        return AsyncMock()

    async def get(self, key):
        return await self.redis.get(key)

    async def set(self, key, value):
        await self.redis.set(key, value)


class MockEventBus:
    async def publish(self, message_type, payload, sender=None, receiver=None):
        logger.info(f"EventBus published: {message_type} -> {receiver} (from {sender}) - {payload}")
    
    def subscribe(self, event_type, callback):
        logger.info(f"EventBus subscribed to: {event_type}")

# --------------------------------------------------------------------------------
# TEST SCENARIOS
# --------------------------------------------------------------------------------

async def run_mock_mode():
    """Run Agent 3 in Mock Mode"""
    logger.info("🚀 Starting Agent 3 Mock Test")
    
    setup_mock_modules()
    from backend.agents.path_planner_agent import PathPlannerAgent, ChainingMode
    
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    agent = PathPlannerAgent("mock_planner", state_manager, event_bus)
    
    # 1. Setup Mock Neo4j Data (Personal Subgraph)
    # ----------------------------------------------------------------------------
    # Concepts: Basics (Known), Loops (Next), Functions (Next), Advanced (Hard)
    state_manager.neo4j.run_query.side_effect = [
        # Query 1: Course Concepts (Personal Subgraph)
        [
            {"concept_id": "Python_Basics", "name": "Python Basics", "difficulty": 1, "time_estimate": 15},
            {"concept_id": "Loops", "name": "Loops", "difficulty": 2, "time_estimate": 30},
            {"concept_id": "Functions", "name": "Functions", "difficulty": 2, "time_estimate": 30},
            {"concept_id": "Classes", "name": "Classes", "difficulty": 3, "time_estimate": 45}
        ],
        # Query 2: Relationships
        [
            {"source": "Python_Basics", "target": "Loops", "rel_type": "NEXT"},
            {"source": "Loops", "target": "Functions", "rel_type": "NEXT"},
            {"source": "Functions", "target": "Classes", "rel_type": "NEXT"},
            {"source": "Classes", "target": "Functions", "rel_type": "REQUIRES"} # Prereq check
        ]
    ]

    # 2. Test Execution (Generate Path)
    # ----------------------------------------------------------------------------
    logger.info("🧪 Testing Path Generation...")
    
    # Patch random to allow gate pass
    with patch('random.random', return_value=0.9): 
        # random > gate_prob (e.g. 1.0) -> Fail? No, logic is:
        # if random.random() > gate_prob: Force BACKWARD.
        # So we want random() <= gate_prob to PASS.
        # If score=0.8, gate_prob=1.0. random 0.9 <= 1.0 -> PASS.
        pass

    # Actually, let's just run it. The logic inside is complex, we just check output validity.
    result = await agent.execute(
        learner_id="test_learner_123",
        goal="Master Python",
        last_result="PROCEED"
    )
    
    if result["success"]:
        print("\n" + "="*50)
        print("[SUCCESS] PATH GENERATED")
        print("="*50)
        print(f"Chain Mode: {result['chain_mode']}")
        print(f"Path Length: {len(result['learning_path'])}")
        for step in result["learning_path"]:
            print(f" - Day {step['day']}: {step['concept_name']} ({step['chain_mode']})")
    else:
        logger.error(f"Path generation failed: {result.get('error')}")
        sys.exit(1)

    # 3. Test Feedback Loop (With Lock)
    # ----------------------------------------------------------------------------
    logger.info("\n🧪 Testing Feedback Loop (Distributed Lock)...")
    
    feedback_event = {
        "concept_id": "Loops",
        "score": 0.9,
        "passed": True,
        "context_vector": [0.1] * 10
    }
    
    # Mock Redis Get/Set for MAB
    state_manager.redis.get.return_value = None # First time
    
    await agent._on_evaluation_feedback(feedback_event)
    
    # Verify Lock Acquisition
    state_manager.redis.lock.assert_called_with(name="lock:concept:Loops", timeout=5)
    logger.info("✅ Redis Lock correctly requested for concept: Loops")


async def run_real_mode():
    """Run Agent 3 in Real Mode (Requires Redis/Neo4j)"""
    logger.info("🚀 Starting Agent 3 Real Test")
    from backend.services.state_manager import StateManager
    from backend.core.event_bus import EventBus
    from backend.agents.path_planner_agent import PathPlannerAgent
    
    state_manager = StateManager()
    await state_manager.connect()
    event_bus = EventBus()
    
    agent = PathPlannerAgent("real_planner", state_manager, event_bus)
    
    # Use an existing learner from your DB
    # Ensure you have run Agent 1 & Agent 2 tests to populate DB!
    learner_id = "user_123" # Replace with valid ID if needed or clean DB
    
    # 1. Create Dummy Profile if needed
    await state_manager.redis.set(f"profile:{learner_id}", json.dumps({
        "learner_id": learner_id,
        "topic": "Python",
        "time_available": 20,
        "hours_per_day": 2
    }))
    
    result = await agent.execute(
        learner_id=learner_id,
        goal="Learn Python Real",
        last_result="PROCEED"
    )
    
    print(json.dumps(result, indent=2, default=str))
    
    if result["success"]:
        logger.info("✅ Real Path Generation Successful")
    else:
        logger.error(f"❌ Real Path Generation Failed: {result.get('error')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mock", "real"], default="mock")
    args = parser.parse_args()
    
    if args.mode == "mock":
        asyncio.run(run_mock_mode())
    else:
        asyncio.run(run_real_mode())
