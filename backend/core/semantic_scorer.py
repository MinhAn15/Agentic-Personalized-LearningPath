"""
Semantic Scorer for Evaluator Agent.

Per THESIS Section 3.5.4:
- LLM-based scoring with double grounding
- Semantic similarity + LLM detailed scoring + Course KG boost
- Confidence based on concept definition clarity
"""

import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class SemanticScorer:
    """
    Score learner answers using semantic similarity + LLM + grounding.
    
    Scoring formula:
    final_score = 0.4 × semantic_sim + 0.5 × llm_score + 0.1 × grounding_boost
    """
    
    def __init__(self, llm_client=None, embedding_model=None, course_kg=None):
        self.llm = llm_client
        self.embeddings = embedding_model
        self.course_kg = course_kg
        self.logger = logging.getLogger(f"{__name__}.SemanticScorer")
    
    async def score_answer(
        self, 
        concept_id: str, 
        learner_answer: str,
        expected_answer: str, 
        grounding_context: dict
    ) -> Tuple[float, float]:
        """
        Score learner's answer using semantic similarity + LLM + Course KG.
        
        Returns:
            (score: 0.0-1.0, confidence: 0.0-1.0)
        """
        try:
            # Handle empty answers
            if not learner_answer or not learner_answer.strip():
                return 0.0, 0.9  # High confidence it's wrong
            
            # Step 1: Semantic similarity baseline
            sim_score = await self._semantic_similarity(learner_answer, expected_answer)
            
            # Step 2: LLM detailed scoring
            llm_score = await self._llm_score(concept_id, learner_answer, expected_answer)
            
            # Step 3: Grounding boost from Course KG
            grounding_boost = self._grounding_boost(concept_id, grounding_context)
            
            # Weighted combination
            final_score = 0.4 * sim_score + 0.5 * llm_score + 0.1 * grounding_boost
            final_score = min(1.0, max(0.0, final_score))
            
            # Confidence: how consistent are our scoring methods?
            score_variance = abs(sim_score - llm_score)
            concept_clarity = grounding_context.get('concept_definition_completeness', 0.5)
            
            # Lower variance = higher confidence; better-defined concept = higher confidence
            confidence = (1.0 - score_variance) * 0.7 + concept_clarity * 0.3
            confidence = min(1.0, max(0.3, confidence))  # Min 0.3, max 1.0
            
            self.logger.info(
                f"Scored {concept_id}: sim={sim_score:.2f}, llm={llm_score:.2f}, "
                f"final={final_score:.2f}, confidence={confidence:.2f}"
            )
            return final_score, confidence
        
        except Exception as e:
            self.logger.exception(f"Error scoring answer: {e}")
            return 0.0, 0.3  # Conservative default
    
    async def _semantic_similarity(self, learner_answer: str, expected_answer: str) -> float:
        """Cosine similarity between embeddings"""
        try:
            if not self.embeddings:
                # Fallback: simple string matching
                return self._string_similarity(learner_answer, expected_answer)
            
            emb_learner = self.embeddings.encode(learner_answer)
            emb_expected = self.embeddings.encode(expected_answer)
            
            # Cosine similarity
            dot = sum(a * b for a, b in zip(emb_learner, emb_expected))
            norm_l = sum(a ** 2 for a in emb_learner) ** 0.5
            norm_e = sum(a ** 2 for a in emb_expected) ** 0.5
            
            similarity = dot / (norm_l * norm_e + 1e-8)
            return max(0.0, (similarity + 1) / 2)  # Normalize to [0, 1]
        except Exception as e:
            self.logger.warning(f"Semantic similarity error: {e}")
            return self._string_similarity(learner_answer, expected_answer)
    
    async def _llm_score(
        self, 
        concept_id: str, 
        learner_answer: str,
        expected_answer: str
    ) -> float:
        """Use LLM for detailed scoring with reasoning"""
        if not self.llm:
            # Fallback to simple comparison
            return self._string_similarity(learner_answer, expected_answer)
        
        prompt = f"""
Compare these two answers for concept {concept_id}:

LEARNER'S ANSWER:
{learner_answer}

EXPECTED ANSWER:
{expected_answer}

Score 0-100 based on:
1. Syntactic correctness (20%)
2. Semantic correctness (40%)
3. Completeness (20%)
4. Efficiency/Best practices (20%)

CRITICAL: Do not hallucinate. If elements are missing or incorrect, score lower.
Respond ONLY with a number 0-100 on the first line, then explain briefly.
"""
        
        try:
            response = await self.llm.acomplete(prompt, max_tokens=150)
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Extract score from first line
            first_line = response_text.split('\n')[0].strip()
            digits = ''.join(c for c in first_line if c.isdigit())
            
            if digits:
                score = int(digits) / 100.0
                return min(1.0, max(0.0, score))
            
            return 0.5  # Default if parsing fails
        except Exception as e:
            self.logger.warning(f"LLM scoring error: {e}")
            return 0.5
    
    def _grounding_boost(self, concept_id: str, grounding_context: dict) -> float:
        """Boost confidence if concept is well-defined in Course KG"""
        if not self.course_kg:
            return grounding_context.get('concept_definition_completeness', 0.5)
        
        try:
            concept_node = self.course_kg.get_node(concept_id)
            if not concept_node:
                return 0.3
            
            score = 0.0
            
            # Check concept definition quality
            if concept_node.get('definition'):
                score += 0.3
            if concept_node.get('examples') and len(concept_node['examples']) >= 2:
                score += 0.3
            if concept_node.get('common_errors'):
                score += 0.2
            if concept_node.get('bloom_level') in ['APPLY', 'ANALYZE', 'EVALUATE']:
                score += 0.2
            
            return min(1.0, score)
        except Exception:
            return 0.5
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Fallback: Levenshtein-based similarity"""
        from difflib import SequenceMatcher
        
        s1_norm = s1.lower().strip()
        s2_norm = s2.lower().strip()
        
        return SequenceMatcher(None, s1_norm, s2_norm).ratio()
