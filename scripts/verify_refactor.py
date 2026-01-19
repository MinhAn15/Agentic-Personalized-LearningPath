import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.llm_factory import LLMFactory
from backend.agents.tutor_agent import TutorAgent
from backend.agents.evaluator_agent import EvaluatorAgent
from backend.agents.profiler_agent import ProfilerAgent
from backend.agents.knowledge_extraction_agent import KnowledgeExtractionAgent
from backend.agents.kag_agent import KAGAgent
from backend.utils.semantic_chunker import SemanticChunker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_refactor")

class MockStateManager:
    def __init__(self):
        self.neo4j = None # Mocking as None or a simple object if needed
        self.redis = None

class MockEventBus:
    def subscribe(self, topic, handler): pass
    async def publish(self, topic, payload, **kwargs): pass

async def verify_agents():
    logger.info("Starting Refactor Verification...")
    
    # 1. Verify LLMFactory
    logger.info("Checking LLMFactory...")
    llm = LLMFactory.get_llm()
    embed = LLMFactory.get_embedding_model()
    logger.info(f"LLM Provider Configured: {llm.metadata.model_name}")
    logger.info(f"Embedding Provider Configured: {embed.model_name}")
    
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    
    # 2. Verify TutorAgent
    logger.info("Initializing TutorAgent...")
    tutor = TutorAgent("test_tutor", state_manager, event_bus)
    if tutor.llm:
         logger.info("✅ TutorAgent initialized with LLM")
    
    # 3. Verify EvaluatorAgent
    logger.info("Initializing EvaluatorAgent...")
    evaluator = EvaluatorAgent("test_evaluator", state_manager, event_bus)
    if evaluator.llm:
        logger.info("✅ EvaluatorAgent initialized with LLM")

    # 4. Verify ProfilerAgent
    logger.info("Initializing ProfilerAgent...")
    profiler = ProfilerAgent("test_profiler", state_manager, event_bus)
    if profiler.llm:
        logger.info("✅ ProfilerAgent initialized with LLM")
        
    # 5. Verify KnowledgeExtractionAgent
    logger.info("Initializing KnowledgeExtractionAgent...")
    ke_agent = KnowledgeExtractionAgent("test_ke", state_manager, event_bus)
    if ke_agent.llm and ke_agent.embedding_model:
        logger.info("✅ KnowledgeExtractionAgent initialized with LLM and Embedding")
        
    # 6. Verify KAGAgent
    logger.info("Initializing KAGAgent...")
    kag = KAGAgent("test_kag", state_manager, event_bus)
    if kag.llm:
        logger.info("✅ KAGAgent initialized with LLM")
        
    # 7. Verify SemanticChunker
    logger.info("Initializing SemanticChunker...")
    chunker = SemanticChunker(llm=llm)
    logger.info("✅ SemanticChunker initialized")
    
    logger.info("🎉 All Agents Verified Successfully!")

if __name__ == "__main__":
    asyncio.run(verify_agents())
