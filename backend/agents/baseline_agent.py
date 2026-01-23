"""
Baseline Agent: Vanilla RAG without SOTA cognitive architectures.

Purpose:
- Serves as the control group for A/B testing against the 6-Agent system
- Implements simple retrieval (Vector Search) + generation without:
  - ToT (Tree of Thoughts)
  - CoT (Chain of Thought)
  - JudgeLM evaluation
  - MemGPT memory management
  
This allows us to measure the value-add of each SOTA architecture.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from backend.core.llm_factory import LLMFactory
from backend.config import get_settings


class BaselineAgent:
    """
    Vanilla RAG Agent for baseline comparison.
    
    Architecture:
    - Standard Vector Search (Top-K)
    - Direct LLM generation without CoT
    - No memory management (stateless)
    - No multi-step planning (greedy single-step)
    """
    
    def __init__(self, agent_id: str = "baseline"):
        self.agent_id = agent_id
        self.settings = get_settings()
        self.logger = logging.getLogger(f"BaselineAgent.{agent_id}")
        
        # Initialize LLM and Embeddings using Factory
        self.llm = LLMFactory.get_llm()
        self.embedding_model = LLMFactory.get_embedding_model()
        
        # Configure LlamaIndex Global Settings
        Settings.llm = self.llm
        Settings.embed_model = self.embedding_model
        
        # Load Vector Store Index
        self.vector_index = self._load_vector_index()
    
    def _load_vector_index(self) -> Optional[VectorStoreIndex]:
        """Load the persisted vector index from Knowledge Extraction phase."""
        try:
            storage_dir = os.path.join(os.getcwd(), "backend", "storage", "vector_store")
            
            if not os.path.exists(storage_dir) or not os.path.exists(os.path.join(storage_dir, "docstore.json")):
                self.logger.warning(f"⚠️ Vector store not found at {storage_dir}. Knowledge Extraction must run first.")
                return None
                
            self.logger.info(f"Loading vector index from {storage_dir}...")
            storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
            index = load_index_from_storage(storage_context)
            self.logger.info("✅ Vector index loaded successfully.")
            return index
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load vector index: {e}")
            return None
    
    async def answer_question(
        self,
        question: str,
        context_override: Optional[str] = None,
        learner_profile: Optional[Dict] = None,
        force_real: bool = False
    ) -> Dict[str, Any]:
        """
        Answer a question using simple RAG (no CoT, no scaffolding).
        """
        self.logger.info(f"Answering question: {question}")
        
        # 1. Retrieval
        retrieved_context = ""
        retrieved_nodes = []
        
        if self.vector_index:
            try:
                # Top-K = 3 for baseline
                retriever = self.vector_index.as_retriever(similarity_top_k=3)
                nodes = await retriever.aretrieve(question)
                retrieved_nodes = [n.get_content() for n in nodes]
                retrieved_context = "\n\n".join(retrieved_nodes)
                self.logger.info(f"📚 Retrieved {len(nodes)} chunks for context.")
            except Exception as e:
                self.logger.error(f"Retrieval failed: {e}")
        
        # Allow override for testing
        final_context = context_override or retrieved_context
        
        # 2. Build Prompt
        prompt = self._build_simple_prompt(question, final_context, learner_profile)
        
        # 3. Generation
        try:
            # Use mock if configured AND formatted not forced to real
            use_mock = self.settings.MOCK_LLM and not force_real
            
            if use_mock:
                response = self._mock_response(question)
            else:
                response = await self.llm.acomplete(prompt)
                response = response.text if hasattr(response, 'text') else str(response)
            
            return {
                "agent": "baseline",
                "question": question,
                "answer": response,
                "retrieved_context_snippets": retrieved_nodes[:2], # Return top 2 snippets for debug
                "reasoning_traces": None,  # No CoT
                "scaffold_type": "direct_answer",
                "metadata": {
                    "architecture": "vanilla_rag",
                    "features_disabled": ["cot", "scaffolding", "socratic", "leakage_guard"],
                    "embedding_model": self.embedding_model.model_name
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return {"error": str(e)}
    
    async def evaluate_response(
        self,
        learner_response: str,
        expected_answer: str,
        concept_id: str = None,
        force_real: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate response using simple scoring (no JudgeLM).
        """
        self.logger.info("Evaluating response with simple scoring...")
        
        prompt = f"""
Rate the following learner response on a scale of 0-100 based on the expected answer.

Expected Answer: {expected_answer}
Learner Response: {learner_response}

Respond with strictly following format:
SCORE: <number 0-100>
JUSTIFICATION: <1 sentence>
"""
        
        try:
            use_mock = self.settings.MOCK_LLM and not force_real
            
            if use_mock:
                score = 65
                justification = "Mock justification"
            else:
                response = await self.llm.acomplete(prompt)
                text = response.text if hasattr(response, 'text') else str(response)
                score, justification = self._parse_evaluation(text)
            
            return {
                "agent": "baseline",
                "score": score,
                "justification": justification,
                "rubric_breakdown": None,
                "metadata": {
                    "architecture": "simple_similarity",
                    "features_disabled": ["judgelm", "cot_grading", "rubric_scoring"],
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating: {e}")
            return {"error": str(e)}
    
    # ------------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------------
    
    def _build_simple_prompt(
        self,
        question: str,
        context: Optional[str],
        profile: Optional[Dict]
    ) -> str:
        """Build a simple prompt without CoT instructions."""
        parts = []
        parts.append("You are a helpful teaching assistant. Answer the question directly and concisely.")
        
        if context:
            parts.append(f"\nREFERENCE INFORMATION:\n{context}")
        
        if profile:
            name = profile.get("name", "Learner")
            parts.append(f"\nStudent Name: {name}")
        
        parts.append(f"\nQUESTION: {question}")
        parts.append("\nANSWER:")
        
        return "\n".join(parts)
    
    def _mock_response(self, question: str) -> str:
        return f"[BASELINE MOCK] Answer to: {question[:50]}..."
    
    def _parse_evaluation(self, text: str):
        """Simple parse of SCORE: X and JUSTIFICATION: Y"""
        import re
        score = 50
        justification = "Could not parse"
        
        s_match = re.search(r"SCORE:\s*(\d+)", text, re.IGNORECASE)
        if s_match:
            score = int(s_match.group(1))
            
        j_match = re.search(r"JUSTIFICATION:\s*(.+)", text, re.IGNORECASE)
        if j_match:
            justification = j_match.group(1).strip()
            
        return score, justification
