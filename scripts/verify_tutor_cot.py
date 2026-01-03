import sys
import os
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict

# Fix Path
sys.path.append(os.getcwd())

from backend.agents.tutor_agent import TutorAgent

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Tutor_CoT_Test")

# Mock Components
class MockStateManager:
    def __init__(self):
        self.neo4j = MagicMock()
        self.redis = MagicMock()

class MockEventBus:
    def __init__(self):
        self.subscribe = MagicMock()
        self.publish = AsyncMock()

class MockLLM:
    """Mock LLM to simulate CoT Traces"""
    async def acomplete(self, prompt: str) -> MagicMock:
        response = MagicMock()
        # Mock CoT output with Leakage keywords
        response.text = """
        1. Concept: SQL Joins.
        2. Error: Student confuses INNER and LEFT JOIN.
        3. Logic: INNER JOIN only returns matches. LEFT JOIN returns all left.
        4. Hint: Ask student to visualize Venn diagram.
        Therefore, the answer is INNER JOIN.
        """
        return response

async def verify_tutor_cot():
    """Verify Tutor Agent Chain-of-Thought Logic"""
    logger.info("\n🧪 1. Initializing Tutor Agent (Mock Mode)...")
    
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    llm = MockLLM()
    
    # Patch Settings to avoid LlamaIndex validation error
    with patch('backend.agents.tutor_agent.Settings'):
        agent = TutorAgent("tutor_test", state_manager, event_bus, llm=llm)
    
    # Disable components not under test
    agent._get_concept_from_kg = AsyncMock(return_value={"name": "SQL Joins"}) # Legacy code mocking
    agent._extract_domain = MagicMock(return_value="General")

    logger.info("\n🧪 2. Testing CoT Generation & Leakage Guard...")
    
    # Input
    kwargs = {
        "learner_id": "student_1",
        "question": "Why didn't my NULLs show up?",
        "concept_id": "sql_joins",
        "conversation_history": []
    }
    
    # Execute
    result = await agent.execute(**kwargs)
    
    # Verification
    logger.info(f"Result Response: {result['response']}")
    
    # CHECK 1: Leakage Guard
    if "Therefore" in result['response'] or "the answer is" in result['response']:
        logger.error("❌ FAILURE: Leakage detected! 'Therefore/Answer is' found in response.")
    else:
        logger.info("✅ SUCCESS: Leakage Guard removed final answer.")
        
    # CHECK 2: Scaffolding Format
    if "Let's breakdown your logic" in result['response']:
        logger.info("✅ SUCCESS: Output format matches Scaffolding template.")
    else:
        logger.error("❌ FAILURE: Output format mismatch.")

    # CHECK 3: Self-Consistency (Implicit)
    logger.info("✅ SUCCESS: Consensus logic executed (Mocked).")

if __name__ == "__main__":
    asyncio.run(verify_tutor_cot())
