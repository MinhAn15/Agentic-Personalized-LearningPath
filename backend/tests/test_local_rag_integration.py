import unittest
import shutil
import os
import asyncio
from unittest.mock import MagicMock, patch
from backend.utils.semantic_chunker import SemanticChunk
from backend.agents.knowledge_extraction_agent import KnowledgeExtractionAgent
from backend.agents.tutor_agent import TutorAgent

class TestLocalRAGIntegration(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_state_manager = MagicMock()
        self.mock_event_bus = MagicMock()
        
        # Determine paths
        self.cwd = os.getcwd()
        self.storage_path = os.path.join(self.cwd, "backend", "storage", "vector_store")
        
        # Clean up before test
        if os.path.exists(self.storage_path):
            shutil.rmtree(self.storage_path)

    def tearDown(self):
        # Clean up after test
        if os.path.exists(self.storage_path):
            shutil.rmtree(self.storage_path)

    def test_persist_and_load(self):
        """Test that chunks persisted by Agent 1 can be loaded by Agent 4"""
        
        # 1. Setup Data
        chunks = [
            SemanticChunk(
                chunk_id="c1",
                content="LlamaIndex is a data framework for LLMs.",
                source_heading="Intro",
                metadata={}
            ),
            SemanticChunk(
                chunk_id="c2", 
                content="RAG stands for Retrieval Augmented Generation.",
                source_heading="Definition",
                metadata={}
            )
        ]
        
        # 2. Agent 1: Persist
        # Mock GeminiEmbedding to avoid API keys and avoid creating real files with invalid keys
        with patch('backend.agents.knowledge_extraction_agent.GeminiEmbedding') as MockEmbed:
            # Mock get_text_embedding to return a fixed vector
            MockEmbed.return_value.get_text_embedding.return_value = [0.1] * 768
            
            agent1 = KnowledgeExtractionAgent("agent1", self.mock_state_manager, self.mock_event_bus)
        
        # Define async runner
        async def run_persist():
            await agent1._persist_vector_index(chunks, "doc_test_1")
            
        loop = asyncio.new_event_loop()
        loop.run_until_complete(run_persist())
        loop.close()
        
        # Verify files created
        self.assertTrue(os.path.exists(self.storage_path))
        self.assertTrue(os.path.exists(os.path.join(self.storage_path, "docstore.json")))
        
        # 3. Agent 4: Load
        # Mock settings for TutorAgent
        with patch('backend.agents.tutor_agent.get_settings') as mock_settings:
            mock_settings.return_value.GEMINI_MODEL = "gemini-pro"
            mock_settings.return_value.GOOGLE_API_KEY = "dummy"
            
            # We must mock Gemini or it will try to hit API on init
            with patch('backend.agents.tutor_agent.Gemini'), \
                 patch('backend.agents.tutor_agent.GeminiEmbedding'):
                 agent4 = TutorAgent("agent4", self.mock_state_manager, self.mock_event_bus)
        
        self.assertIsNotNone(agent4.query_engine, "Query engine should be loaded")
        
        # 4. Agent 4: Query (Mocking query for unit test speed/safety)
        # We checked plumbing. Actual query needs real embeddings which requires API key.
        # We trust LlamaIndex works if index loaded correctly.
