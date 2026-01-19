"""
Baseline Agent: Vanilla RAG without SOTA cognitive architectures.

Purpose:
- Serves as the control group for A/B testing against the 6-Agent system
- Implements simple retrieval + generation without:
  - ToT (Tree of Thoughts)
  - CoT (Chain of Thought)
  - JudgeLM evaluation
  - MemGPT memory management
  
This allows us to measure the value-add of each SOTA architecture.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from backend.core.llm_factory import LLMFactory
from backend.config import get_settings


class BaselineAgent:
    """
    Vanilla RAG Agent for baseline comparison.
    
    Architecture:
    - Simple retrieval from vector store
    - Direct LLM generation without CoT
    - No memory management (stateless)
    - No multi-step planning (greedy single-step)
    """
    
    def __init__(self, agent_id: str = "baseline"):
        self.agent_id = agent_id
        self.settings = get_settings()
        self.llm = LLMFactory.get_llm()
        self.logger = logging.getLogger(f"BaselineAgent.{agent_id}")
    
    async def answer_question(
        self,
        question: str,
        context: Optional[str] = None,
        learner_profile: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Answer a question using simple RAG (no CoT, no scaffolding).
        
        Unlike TutorAgent:
        - No hidden reasoning traces
        - No Socratic questioning
        - No leakage guard
        - Direct answer generation
        """
        self.logger.info(f"Answering question: {question[:50]}...")
        
        # Build simple prompt (no CoT)
        prompt = self._build_simple_prompt(question, context, learner_profile)
        
        try:
            if self.settings.MOCK_LLM:
                response = self._mock_response(question)
            else:
                response = await self.llm.acomplete(prompt)
                response = response.text if hasattr(response, 'text') else str(response)
            
            return {
                "agent": "baseline",
                "question": question,
                "answer": response,
                "reasoning_traces": None,  # No CoT
                "scaffold_type": "direct_answer",  # No scaffolding
                "metadata": {
                    "architecture": "vanilla_rag",
                    "features_disabled": ["cot", "scaffolding", "socratic", "leakage_guard"],
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return {"error": str(e)}
    
    async def evaluate_response(
        self,
        learner_response: str,
        expected_answer: str,
        concept_id: str = None
    ) -> Dict[str, Any]:
        """
        Evaluate response using simple scoring (no JudgeLM).
        
        Unlike EvaluatorAgent:
        - No reference-as-prior
        - No CoT grading trace
        - Simple similarity-based scoring
        """
        self.logger.info("Evaluating response with simple scoring...")
        
        # Simple prompt for evaluation
        prompt = f"""
Rate the following learner response on a scale of 0-100.

Expected Answer: {expected_answer}
Learner Response: {learner_response}

Respond with only a number (0-100).
"""
        
        try:
            if self.settings.MOCK_LLM:
                score = 65  # Mock score
            else:
                response = await self.llm.acomplete(prompt)
                response_text = response.text if hasattr(response, 'text') else str(response)
                score = self._extract_score(response_text)
            
            return {
                "agent": "baseline",
                "score": score,
                "justification": None,  # No JudgeLM trace
                "rubric_breakdown": None,  # No multi-dimensional scoring
                "metadata": {
                    "architecture": "simple_similarity",
                    "features_disabled": ["judgelm", "cot_grading", "rubric_scoring"],
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating: {e}")
            return {"error": str(e)}
    
    async def plan_next_lesson(
        self,
        learner_id: str,
        available_concepts: List[str],
        mastery_map: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Plan next lesson using greedy selection (no ToT).
        
        Unlike PathPlannerAgent:
        - No beam search
        - No multi-step lookahead
        - Greedy: pick lowest mastery concept
        """
        self.logger.info(f"Planning next lesson for {learner_id} (greedy)...")
        
        # Greedy: select concept with lowest mastery
        if not available_concepts:
            return {"next_concept": None, "reason": "No concepts available"}
        
        concept_scores = {c: mastery_map.get(c, 0.0) for c in available_concepts}
        next_concept = min(concept_scores, key=concept_scores.get)
        
        return {
            "agent": "baseline",
            "next_concept": next_concept,
            "selection_method": "greedy_lowest_mastery",
            "lookahead_depth": 0,  # No ToT
            "beam_width": 1,  # Single path
            "metadata": {
                "architecture": "greedy",
                "features_disabled": ["tot", "beam_search", "state_evaluator"],
            }
        }
    
    def _build_simple_prompt(
        self,
        question: str,
        context: Optional[str],
        profile: Optional[Dict]
    ) -> str:
        """Build a simple prompt without CoT instructions."""
        parts = ["Answer the following question directly and concisely."]
        
        if context:
            parts.append(f"\nContext:\n{context}")
        
        parts.append(f"\nQuestion: {question}")
        parts.append("\nAnswer:")
        
        return "\n".join(parts)
    
    def _mock_response(self, question: str) -> str:
        """Generate mock response for testing."""
        return f"[BASELINE MOCK] Answer to: {question[:50]}..."
    
    def _extract_score(self, text: str) -> int:
        """Extract numeric score from LLM response."""
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            score = int(numbers[0])
            return min(100, max(0, score))
        return 50  # Default


# =============================================
# COMPARISON UTILITIES
# =============================================

async def compare_responses(
    question: str,
    context: str,
    baseline_agent: BaselineAgent,
    tutor_agent  # TutorAgent instance
) -> Dict[str, Any]:
    """
    Run the same question through both agents for comparison.
    Returns structured comparison data.
    """
    from backend.models.schemas import TutorInput
    
    # Baseline response
    baseline_result = await baseline_agent.answer_question(question, context)
    
    # SOTA response (TutorAgent with CoT)
    tutor_input = TutorInput(
        learner_id="comparison_learner",
        question=question,
        concept_id="comparison_concept",
        force_real=True
    )
    sota_result = await tutor_agent.execute(tutor_input=tutor_input)
    
    return {
        "question": question,
        "baseline": baseline_result,
        "sota": sota_result,
        "comparison": {
            "baseline_has_cot": baseline_result.get("reasoning_traces") is not None,
            "sota_has_cot": sota_result.get("cot_traces") is not None,
        }
    }
