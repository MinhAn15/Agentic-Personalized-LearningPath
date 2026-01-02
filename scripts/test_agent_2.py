import asyncio
import os
import sys
import logging
import argparse
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Agent2_TestRunner")

# ==========================================
# HOTFIX: MOCK SIBLING AGENTS
# ==========================================
sys.modules["backend.agents.knowledge_extraction_agent"] = MagicMock()
sys.modules["backend.agents.path_planner_agent"] = MagicMock()
sys.modules["backend.agents.tutor_agent"] = MagicMock()
sys.modules["backend.agents.evaluator_agent"] = MagicMock()
sys.modules["backend.agents.kag_agent"] = MagicMock()

# Mock LlamaIndex for standalone testing
sys.modules["llama_index"] = MagicMock()
sys.modules["llama_index.llms"] = MagicMock()
sys.modules["llama_index.llms.gemini"] = MagicMock()
sys.modules["llama_index.core"] = MagicMock()
sys.modules["llama_index.graph_stores"] = MagicMock()
sys.modules["llama_index.graph_stores.neo4j"] = MagicMock()
sys.modules["llama_index.embeddings"] = MagicMock()
sys.modules["llama_index.embeddings.gemini"] = MagicMock()

class MockStateManager:
    def __init__(self):
        self.neo4j = AsyncMock()
        self.redis = AsyncMock()
        self.postgres = AsyncMock()
        
        # Setup mock returns
        self.neo4j.run_query.return_value = []
        
        # Mock Redis Lock
        lock_mock = MagicMock()
        
        async def async_acquire():
            return True
            
        async def async_release():
            pass
            
        lock_mock.acquire = async_acquire
        lock_mock.release = async_release
        self.redis.lock.return_value = lock_mock
        
    async def get(self, key):
        if "profile:" in key:
            return {
                "learner_id": "test_learner",
                "name": "Test User",
                "concept_mastery_map": {},
                "avg_mastery_level": 0.5
            }
        return None
        
    async def set(self, key, value, ttl=None):
        return True

class MockEventBus:
    async def publish(self, *args, **kwargs):
        logger.info(f"event_bus.publish called with: {kwargs}")

    def subscribe(self, message_type, handler):
        logger.info(f"event_bus.subscribe called for: {message_type}")

async def run_mock_mode():
    """Test Logic in Isolation"""
    from backend.agents.profiler_agent import ProfilerAgent
    
    logger.info("🎭 Initializing MOCK environment...")
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    
    agent = ProfilerAgent(
        agent_id="mock_profiler_1",
        state_manager=state_manager,
        event_bus=event_bus
    )
    
    # 1. Mock LLM for Intent Extraction
    agent.llm.acomplete = AsyncMock(return_value=MagicMock(text='''
    {
      "topic": "Python",
      "purpose": "Data Science",
      "goal": "Learn Python for Data Science",
      "time_available": 30,
      "current_skill_level": "BEGINNER",
      "preferred_learning_style": "VISUAL"
    }
    '''))
    
    # 2. Mock Diagnostic Assessment (Skip for speed or mock return)
    # We will just verify the profile creation flow
    
    payload = {
        "learner_message": "I want to learn Python for Data Science",
        "learner_name": "Test User",
        "skip_diagnostic": True # Skip complex graph RAG
    }
    
    logger.info("🚀 Executing Agent 2 (Mock Mode)...")
    result = await agent.execute(**payload)
    
    print("\n" + "="*50)
    print("[SUCCESS] PROFILING RESULT")
    print("="*50)
    import json
    print(json.dumps(result, indent=2, default=str))
    
    # 3. Test Event Handling (EVALUATION_COMPLETED)
    logger.info("\n🧪 Testing Event: EVALUATION_COMPLETED...")
    event_payload = {
        "learner_id": result.get("learner_id", "test_learner"),
        "concept_id": "python_basics",
        "score": 0.9,
        "question_difficulty": 1,
        "question_type": "factual"
    }
    
    await agent._on_evaluation_completed(event_payload)
    logger.info("Event handler executed successfully (Check logs for lock acquisition).")

async def run_real_mode():
    """Run with Real DBs"""
    try:
        from backend.database.database_factory import initialize_databases, get_factory
        from backend.core.state_manager import CentralStateManager
        from backend.core.event_bus import EventBus
        from backend.agents.profiler_agent import ProfilerAgent
        
        await initialize_databases()
        factory = get_factory()
        state_manager = CentralStateManager(factory.redis, factory.postgres)
        state_manager.neo4j = factory.neo4j
        
        agent = ProfilerAgent(
            agent_id="real_profiler",
            state_manager=state_manager,
            event_bus=EventBus()
        )
        
        payload = {
            "learner_message": "I want to master Advance SQL in 1 week",
            "learner_name": "Real User",
            "skip_diagnostic": False 
        }
        
        result = await agent.execute(**payload)
        print(result)
        
    except Exception as e:
        logger.error(f"Real mode failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["real", "mock"], default="mock")
    args = parser.parse_args()
    
    if args.mode == "real":
        asyncio.run(run_real_mode())
    else:
        asyncio.run(run_mock_mode())
