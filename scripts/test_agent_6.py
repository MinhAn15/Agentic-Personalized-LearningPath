import asyncio
import logging
import argparse
import sys
import json
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

from backend.agents.kag_agent import KAGAgent
from backend.models.artifacts import ArtifactType

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Agent6_TestRunner")

# Mock State Manager and Neo4j
class MockStateManager:
    def __init__(self):
        self.redis = MagicMock()
        self.neo4j = AsyncMock()
        self.neo4j.run_query = AsyncMock(return_value=[]) # Default empty
    
    async def get_state(self, entity_id, state_type):
        return {}

# Mock Event Bus
class MockEventBus:
    async def publish(self, message_type, payload, sender=None, receiver=None):
        logger.info(f"EventBus published: {message_type} -> {receiver} (from {sender})")
    
    def subscribe(self, event_type, callback):
        logger.info(f"EventBus subscribed to: {event_type}")

    async def send_message(self, receiver, message_type, payload):
        logger.info(f"Sending message: {message_type} -> {receiver} | Payload: {payload}")

# Mock LLM for Atomic Note Extraction
class MockLLM:
    async def acomplete(self, prompt: str):
        # Return a valid JSON for atomic note
        return MagicMock(text=json.dumps({
            "key_insight": "SQL WHERE filters rows based on conditions.",
            "personal_example": "Like filtering a spreadsheet by column value.",
            "common_mistake": "Confusing WHERE with HAVING.",
            "connections": ["SQL_SELECT", "PREDICATE_LOGIC"]
        }))

# ------------------------------------------------------------------------
# MOCK MODE
# ------------------------------------------------------------------------
async def run_mock_mode():
    logger.info("🚀 Starting Agent 6 Mock Test")
    
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    llm = MockLLM()
    
    agent = KAGAgent("mock_kag", state_manager, event_bus, llm=llm, course_kg=MagicMock())
    
    # 1. Test Atomic Note Extraction & Artifact Generation
    logger.info("\n🧪 Testing Zettelkasten Generation...")
    
    # Mock Neo4j responses for creation check
    # 1. Check for related notes (empty)
    # 2. Create node
    # 3. Create links
    state_manager.neo4j.run_query.side_effect = [
        [], # No related notes initially found via query
        [], # Create node result
        []  # Link creation result
    ]
    
    res_artifact = await agent._generate_artifact(
        learner_id="learner1",
        concept_id="SQL_WHERE",
        session_data={
            "question": "What does WHERE do?",
            "answer": "It filters rows.",
            "score": 1.0
        }
    )
    
    logger.info(f"Artifact Type: {res_artifact['artifact_type']} (Expected: ATOMIC_NOTE)")
    assert res_artifact['success'] == True
    assert res_artifact['artifact_type'] == ArtifactType.ATOMIC_NOTE.value
    assert "SQL_SELECT" in res_artifact['tags']
    
    # 2. Test System Analysis (Statistics)
    logger.info("\n🧪 Testing System Learning Analysis...")
    
    # Mock data for 5 learners
    # Learner 1: 0.2 (Struggle)
    # Learner 2: 0.3 (Struggle)
    # Learner 3: 0.9 (Mastered)
    # Learner 4: 0.4 (Struggle)
    # Learner 5: 0.8 (Mastered)
    # Avg: 0.52. Struggle Rate: 3/5 = 0.6
    
    mock_learner_graphs = [
        {"learner1": {"SQL_JOIN": 0.2}},
        {"learner2": {"SQL_JOIN": 0.3}},
        {"learner3": {"SQL_JOIN": 0.1}}, # Changed to struggler -> Avg < 0.4
        {"learner4": {"SQL_JOIN": 0.4}},
        {"learner5": {"SQL_JOIN": 0.4}}
    ]
    
    # Patch the _retrieve_all_learner_graphs method to avoid Neo4j complexity
    with patch.object(agent, '_retrieve_all_learner_graphs', new=AsyncMock(return_value=mock_learner_graphs)):
        res_analysis = await agent._analyze_system(min_learners=5)
        
        stats = res_analysis['statistics'].get('SQL_JOIN', {})
        logger.info(f"Avg Mastery: {stats.get('avg_mastery'):.2f} (Expected: 0.28)")
        logger.info(f"Struggle Rate: {stats.get('struggle_rate'):.2f} (Expected: 1.00)")
        
        assert abs(stats.get('avg_mastery') - 0.28) < 0.01
        assert stats.get('struggle_rate') == 1.0
        
        # Check if recommendations were generated
        recommendations = res_analysis['recommendations']
        logger.info(f"Recommendations generated: {len(recommendations)}")
        assert len(recommendations) > 0
        assert "PRIORITY" in recommendations[0]

    logger.info("\n✅ MOCK TEST PASSED")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['mock', 'real'], default='mock')
    args = parser.parse_args()
    
    if args.mode == 'mock':
        asyncio.run(run_mock_mode())
    else:
        logger.warning("Real mode not fully configured for unit test run.")
