import asyncio
import os
import sys
import logging
import argparse
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Agent1_TestRunner")

# ==========================================
# HOTFIX: MOCK SIBLING AGENTS TO AVOID IMPORT ERRORS
# This allows running Agent 1 tests without installing dependencies for Agent 2, 3, etc.
# ==========================================
sys.modules["backend.agents.profiler_agent"] = MagicMock()
sys.modules["backend.agents.path_planner_agent"] = MagicMock()
sys.modules["backend.agents.tutor_agent"] = MagicMock()
sys.modules["backend.agents.evaluator_agent"] = MagicMock()
sys.modules["backend.agents.kag_agent"] = MagicMock()
# Mock entire packages inside backend.agents if needed, but file-level mock is usually enough

class MockStateManager:
    def __init__(self):
        self.neo4j = AsyncMock()
        self.redis = AsyncMock()
        self.postgres = AsyncMock()
        
        # Setup mock returns
        self.neo4j.run_query.return_value = []
        self.redis.get = AsyncMock(return_value=None)
        self.redis.set = AsyncMock(return_value=True)

    async def get(self, key):
        return None
        
    async def set(self, key, value, ttl=None):
        return True

class MockEventBus:
    async def publish(self, *args, **kwargs):
        logger.info(f"event_bus.publish called with: {kwargs}")

    def subscribe(self, message_type, handler):
        logger.info(f"event_bus.subscribe called for: {message_type}")
    
    def subscribe_sync(self, message_type, handler):
        # Fallback if agent uses sync subscription (unlikely but safe to have)
        pass

async def run_real_mode(document_content, document_title):
    """Run with REAL database connections defined in .env"""
    try:
        from backend.database.database_factory import get_factory, initialize_databases
        from backend.core.state_manager import CentralStateManager
        from backend.core.event_bus import EventBus
        from backend.agents.knowledge_extraction_agent import KnowledgeExtractionAgent
        
        logger.info("🔌 Initializing REAL databases...")
        if not await initialize_databases():
            logger.error("Failed to initialize databases")
            return

        factory = get_factory()
        state_manager = CentralStateManager(factory.redis, factory.postgres)
        state_manager.neo4j = factory.neo4j # Inject Neo4j
        
        event_bus = EventBus()
        
        agent = KnowledgeExtractionAgent(
            agent_id="test_runner_1",
            state_manager=state_manager,
            event_bus=event_bus
        )
        
        payload = {
            "document_content": document_content,
            "document_title": document_title,
            "domain": "test_domain" # Test Dynamic Domain
        }
        
        logger.info("🚀 Executing Agent 1 (Real Mode)...")
        result = await agent.execute(**payload) # Fix: Unpack kwargs
        
        print("\n" + "="*50)
        print("✅ EXECUTION RESULT (Real Mode)")
        print("="*50)
        print(result)
        
        # Clean up would be good here but script will exit
        
    except ImportError as e:
        logger.error(f"Missing dependencies for Real mode: {e}")
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)

async def run_mock_mode(document_content, document_title):
    """Run with MOCK StateManager and EventBus"""
    from backend.agents.knowledge_extraction_agent import KnowledgeExtractionAgent
    
    logger.info("🎭 Initializing MOCK environment...")
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    
    # Mock specific Neo4j calls if needed
    state_manager.neo4j.run_query.return_value = [] # Return empty for concept lookups
    
    # PATCH SemanticChunker to avoid LLM requirement during Init
    with patch("backend.agents.knowledge_extraction_agent.SemanticChunker") as MockChunkerClass:
        # Configure the mock instance returned by the class
        mock_chunker_instance = MagicMock()
        MockChunkerClass.return_value = mock_chunker_instance
        
        agent = KnowledgeExtractionAgent(
            agent_id="mock_runner_1",
            state_manager=state_manager,
            event_bus=event_bus
        )
        
        # We also need to mock the llm_service if it's used elsewhere
        agent.llm = AsyncMock()
        agent.llm.acomplete = AsyncMock(return_value=MagicMock(text="{}"))
        
        # Re-assign chunker (though patch should have verified it)
        agent.chunker = mock_chunker_instance
    
    # Mock internal methods to avoid needing real LLM if we want pure logic test
    
    # Mock internal methods to avoid needing real LLM if we want pure logic test
    # But usually we want to test the flow, so we might let LLM calls fail or mock them too.
    # For now, we assume LLM works or we just see it fail gracefully.
    # To truly mock LLM, we'd need to mock 'agent.llm_service'
    
    # Setting up a mock LLM response for _extract_concepts_from_chunk
    # Updated to match new signature: (chunk, document_title, domain)
    agent._extract_concepts_from_chunk = AsyncMock(return_value=[
        {
            "concept_id": "TestConcept", 
            "name": "Test Concept", 
            "description": "A concept for testing", 
            "type": "concept"
        }
    ])
    # Updated to match new signature: (chunk, concepts, domain)
    agent._extract_relationships_from_chunk = AsyncMock(return_value=[
        {
            "source": "Test Concept", 
            "target": "Other Concept", 
            "relationship_type": "RELATED_TO",
            "keywords": ["mock_theme", "testing"],
            "summary": "Mock summary of relationship"
        }
    ])
    agent._extract_content_keywords = AsyncMock(return_value=["Mock Theme A", "Mock Theme B"])
    # Updated to match new signature: (concepts, domain) - lambda needs 2 args
    agent._enrich_metadata = AsyncMock(side_effect=lambda concepts, domain=None: concepts)
    agent._extract_domain = AsyncMock(return_value="mock_domain")

    # Mock RAG Vector Persistence to avoid real Embedding API calls
    agent._persist_vector_index = AsyncMock()
    
    # Mock Chunker to avoid real Chunking/LLM
    from backend.utils.semantic_chunker import SemanticChunk
    mock_chunk = MagicMock(spec=SemanticChunk)
    mock_chunk.chunk_id = "test_chunk_1"
    mock_chunk.content = "Test content"
    mock_chunk.source_heading = "Test Heading"
    
    # Mock Chunker to avoid real Chunking/LLM
    from backend.utils.semantic_chunker import SemanticChunk
    mock_chunk = MagicMock(spec=SemanticChunk)
    mock_chunk.chunk_id = "test_chunk_1"
    mock_chunk.content = "Test content"
    mock_chunk.source_heading = "Test Heading"
    
    # Configure the mocked chunker (which is agent.chunker)
    agent.chunker.chunk_with_ai = AsyncMock(return_value=[mock_chunk])
    agent.chunker.get_stats.return_value = {"count": 1}
    
    payload = {
        "document_content": document_content,
        "document_title": document_title,
        "domain": "mock_override"
    }
    
    logger.info("🚀 Executing Agent 1 (Mock Mode)...")
    result = await agent.execute(**payload) # Fix: Unpack kwargs
    
    print("\n" + "="*50)
    print("✅ EXECUTION RESULT (Mock Mode)")
    print("="*50)
    import json
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent 1 Test Runner")
    parser.add_argument("--mode", choices=["real", "mock"], default="mock", help="Execution mode")
    parser.add_argument("--file", help="Path to text file to ingest")
    args = parser.parse_args()
    
    content = "This is a sample lecture content about ReactJS hooks and state management."
    title = "Test Document"
    
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
        title = os.path.basename(args.file)
        
    if args.mode == "real":
        asyncio.run(run_real_mode(content, title))
    else:
        asyncio.run(run_mock_mode(content, title))
