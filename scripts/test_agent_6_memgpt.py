
import pytest
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import MagicMock, AsyncMock, patch
from backend.agents.kag_agent import KAGAgent

class MockLLM:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    async def acomplete(self, prompt):
        response = self.responses[self.call_count]
        self.call_count = min(self.call_count + 1, len(self.responses) - 1)
        return MagicMock(text=response)

@pytest.mark.asyncio
async def test_memgpt_heartbeat_loop():
    # Setup Mock LLM to simulate a function call chain
    # Turn 1: Call core_memory_append (Heartbeat)
    # Turn 2: Call archival_memory_search (Heartbeat)
    # Turn 3: Final Answer (Yield)
    mock_llm = MockLLM([
        "[FUNCTION] core_memory_append(\"User Profile\", \"Learner prefers Python.\")",
        "[FUNCTION] archival_memory_search(\"Python basics\")",
        "I have updated your profile and searched for Python basics."
    ])
    
    # Setup Agent
    mock_state_manager = MagicMock()
    # Mock Neo4j for archival search
    mock_state_manager.neo4j.run_query = AsyncMock(return_value=[{"content": "Python is a snake.", "created_at": "2024-01-01"}])
    
    agent = KAGAgent("agent_6", mock_state_manager, MagicMock(), llm=mock_llm)
    
    # Execute User Task
    result = await agent.execute(action="chat", message="Hi, remember I like Python.")
    
    # Assertions
    # 1. Verify Core Memory Updated
    assert "Learner prefers Python." in agent.working_memory.core_memory.get("User Profile", "")
    
    # 2. Verify Archival Search Triggered
    mock_state_manager.neo4j.run_query.assert_called()
    
    # 3. Verify Final Response
    assert "I have updated" in result["response"]
    
    # 4. Verify Context Queue evolution
    # Queue should contain: User Msg -> Funct Call 1 -> Funct Output 1 -> Funct Call 2 -> Funct Out 2 -> Asst Msg
    assert len(agent.working_memory.fifo_queue) >= 5
    print("✅ Heartbeat Loop Verified")

@pytest.mark.asyncio
async def test_memory_pressure_interrupt():
    # Setup Mock LLM
    mock_llm = MagicMock()
    mock_llm.acomplete = AsyncMock(return_value=MagicMock(text="Acknowledged."))

    # Setup Agent with small token limit to trigger pressure
    # Pass mock_llm to avoid Pydantic validation errors on real Gemini class
    agent = KAGAgent("agent_6", MagicMock(), MagicMock(), llm=mock_llm)
    agent.working_memory.max_tokens = 10  # Very small limit
    
    # Inject a large system instruction to trigger pressure immediately
    agent.working_memory.set_system_instructions("A" * 100)
    
    # Mock Auto-Archive
    with patch.object(agent, '_auto_archive', new_callable=AsyncMock) as mock_archive:
        # Execute
        await agent.execute(action="chat", message="trigger")
        
        # Assert _auto_archive called
        mock_archive.assert_called()
        print("✅ Memory Pressure Interrupt Verified")

if __name__ == "__main__":
    # Manually run async tests using asyncio.run
    async def main():
        await test_memgpt_heartbeat_loop()
        await test_memory_pressure_interrupt()
        
    asyncio.run(main())
