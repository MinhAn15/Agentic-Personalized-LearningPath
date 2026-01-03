import asyncio
import logging
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Fix Path to include backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.kag_agent import KAGAgent
from backend.core.event_bus import EventBus

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MemGPT_Test")

# Mocks
class MockStateManager:
    def __init__(self):
        self.neo4j = MagicMock()
        self.neo4j.run_query = AsyncMock(return_value=[])

class MockEventBus:
    def publish(self, channel, message):
        pass
    def subscribe(self, channel, callback):
        pass

class MockLLM:
    def __init__(self):
        self.acomplete = AsyncMock(return_value=MagicMock(text="{}"))

async def verify_memgpt():
    logger.info("🧪 Starting MemGPT Verification...")
    
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    llm = MockLLM()
    
    # Patch Settings
    with patch('backend.agents.kag_agent.get_settings'), \
         patch('backend.agents.kag_agent.Gemini'), \
         patch('backend.agents.kag_agent.AtomicNoteGenerator'), \
         patch('backend.agents.kag_agent.KGSynchronizer'):
         
        agent = KAGAgent("kag_test", state_manager, event_bus, llm=llm)
        
        # Test 1: Working Memory Pressure Trigger
        logger.info("\n🧪 Test 1: Memory Pressure Trigger")
        
        # Artificial pressure fill
        agent.working_memory.max_tokens = 100
        agent.working_memory.add("A long string that will definitely exceed the 70% threshold of 100 tokens. " * 5)
        
        assert agent.working_memory.is_pressure_high() == True, "Memory pressure detection failed"
        logger.info("✅ Pressure detection passed.")
        
        # Monitor Loop Execution (Should trigger auto-archive)
        # Mock _auto_archive to track calls
        agent._auto_archive = AsyncMock(wraps=agent._auto_archive)
        
        await agent.execute(action="analyze", analysis_depth="shallow")
        
        if agent._auto_archive.called:
            logger.info("✅ Auto-archive triggered by pressure monitor.")
        else:
            logger.error("❌ Auto-archive NOT triggered!")
            assert False, "Auto-archive failed"
            
        # Test 2: Heartbeat Recursion
        logger.info("\n🧪 Test 2: Heartbeat Recursion")
        
        # Mock _analyze_system to return heartbeat=True once
        # Using side_effect to return True first, then False
        agent._analyze_system = AsyncMock(side_effect=[
            {"success": True, "request_heartbeat": True, "steps": 1},
            {"success": True, "request_heartbeat": False, "steps": 2}
        ])
        
        result = await agent.execute(action="analyze")
        
        # Should have called _analyze_system twice
        call_count = agent._analyze_system.call_count
        logger.info(f"Analyze called {call_count} times.")
        
        assert call_count == 2, f"Expected 2 calls (Heartbeat), got {call_count}"
        logger.info("✅ Heartbeat recursion verified.")

    logger.info("\n🎉 All MemGPT tests passed!")

if __name__ == "__main__":
    try:
        asyncio.run(verify_memgpt())
    except Exception as e:
        logger.error(f"Test Failed: {e}")
        exit(1)
