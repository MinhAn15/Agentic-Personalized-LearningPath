"""
Error Classifier for Evaluator Agent.

Per THESIS Section 3.5.4:
- Decision tree classification
- 5 error types: CORRECT, CARELESS, INCOMPLETE, PROCEDURAL, CONCEPTUAL
- Ontology-based misconception detection
"""

import logging
from typing import List, Tuple
from difflib import SequenceMatcher

from backend.models.evaluation import ErrorType, Misconception

logger = logging.getLogger(__name__)


class ErrorClassifier:
    """
    Classify errors using decision tree + Course KG ontology.
    
    Decision tree:
    - score >= 0.95: CORRECT
    - score >= 0.80: CARELESS (typos) or INCOMPLETE (missing minor)
    - score >= 0.60: PROCEDURAL or INCOMPLETE
    - score < 0.60: CONCEPTUAL or PROCEDURAL
    """
    
    def __init__(self, course_kg=None, embedding_model=None):
        self.course_kg = course_kg
        self.embeddings = embedding_model
        self.logger = logging.getLogger(f"{__name__}.ErrorClassifier")
    
    async def classify(
        self, 
        learner_answer: str, 
        expected_answer: str,
        score: float, 
        concept_id: str
    ) -> Tuple[ErrorType, List[Misconception]]:
        """
        Classify error type using decision tree.
        
        Returns:
            (error_type, suspected_misconceptions)
        """
        
        # Decision tree based on score thresholds
        if score >= 0.95:
            return ErrorType.CORRECT, []
        
        elif score >= 0.80:
            if await self._is_careless_mistake(learner_answer, expected_answer):
                return ErrorType.CARELESS, []
            else:
                return ErrorType.INCOMPLETE, []
        
        elif score >= 0.60:
            if await self._is_procedural_error(learner_answer, expected_answer, concept_id):
                misconceptions = await self._detect_misconceptions(
                    learner_answer, concept_id, 'PROCEDURAL'
                )
                return ErrorType.PROCEDURAL, misconceptions
            else:
                return ErrorType.INCOMPLETE, []
        
        else:  # score < 0.60
            sim = await self._semantic_similarity(learner_answer, expected_answer)
            if sim < 0.3:
                misconceptions = await self._detect_misconceptions(
                    learner_answer, concept_id, 'CONCEPTUAL'
                )
                if misconceptions:
                    return ErrorType.CONCEPTUAL, misconceptions
                else:
                    return ErrorType.PROCEDURAL, []
            else:
                return ErrorType.INCOMPLETE, []
    
    async def _is_careless_mistake(self, learner: str, expected: str) -> bool:
        """Detect typos, case sensitivity, whitespace issues"""
        # Simple string similarity for typos
        similarity = self._string_similarity(learner, expected)
        if similarity >= 0.90:
            return True
        
        # Check for minor differences (case, whitespace)
        learner_norm = learner.lower().replace(' ', '').replace('\n', '')
        expected_norm = expected.lower().replace(' ', '').replace('\n', '')
        if learner_norm == expected_norm:
            return True
        
        # Check for arithmetic mistakes (if numeric)
        try:
            learner_nums = [float(x) for x in learner.split() if self._is_number(x)]
            expected_nums = [float(x) for x in expected.split() if self._is_number(x)]
            if learner_nums and expected_nums and len(learner_nums) == len(expected_nums):
                # Allow small numeric differences
                if all(abs(l - e) <= 1 for l, e in zip(learner_nums, expected_nums)):
                    return True
        except:
            pass
        
        return False
    
    def _is_number(self, s: str) -> bool:
        """Check if string is a number"""
        try:
            float(s.replace(',', ''))
            return True
        except:
            return False
    
    async def _is_procedural_error(
        self, 
        learner: str, 
        expected: str,
        concept_id: str
    ) -> bool:
        """Check if order of operations or syntax structure is wrong"""
        learner_upper = learner.upper()
        expected_upper = expected.upper()
        
        # SQL-specific: check for wrong keyword order
        sql_keyword_pairs = [
            ("SELECT", "FROM"),
            ("FROM", "WHERE"),
            ("WHERE", "GROUP BY"),
            ("GROUP BY", "HAVING"),
            ("HAVING", "ORDER BY")
        ]
        
        for kw1, kw2 in sql_keyword_pairs:
            pos_l1, pos_l2 = learner_upper.find(kw1), learner_upper.find(kw2)
            pos_e1, pos_e2 = expected_upper.find(kw1), expected_upper.find(kw2)
            
            # Check if order is reversed in learner's answer
            if (pos_l1 >= 0 and pos_l2 >= 0 and pos_e1 >= 0 and pos_e2 >= 0):
                if (pos_l1 > pos_l2) != (pos_e1 > pos_e2):
                    return True
        
        # Check for missing keywords that exist in expected
        for keyword in ["SELECT", "FROM", "WHERE", "JOIN", "GROUP BY"]:
            if keyword in expected_upper and keyword not in learner_upper:
                return True
        
        return False
    
    async def _detect_misconceptions(
        self, 
        learner_answer: str,
        concept_id: str, 
        error_category: str
    ) -> List[Misconception]:
        """Match against Course KG misconception ontology"""
        if not self.course_kg:
            return []
        
        try:
            concept_node = self.course_kg.get_node(concept_id)
            if not concept_node or 'common_errors' not in concept_node:
                return self._get_default_misconceptions(error_category, learner_answer)
            
            detected = []
            for error_entry in concept_node.get('common_errors', []):
                entry_category = error_entry.get('category', '').upper()
                
                if error_category.upper() in entry_category or not entry_category:
                    similarity = await self._semantic_similarity(
                        learner_answer,
                        error_entry.get('description', '')
                    )
                    
                    if similarity >= 0.65:
                        misconception = Misconception(
                            type=error_entry.get('type', 'unknown'),
                            description=error_entry.get('description', ''),
                            severity='HIGH' if error_category == 'CONCEPTUAL' else 'MEDIUM',
                            confidence=similarity,
                            evidence=learner_answer[:200]
                        )
                        detected.append(misconception)
            
            return detected
        except Exception as e:
            self.logger.warning(f"Misconception detection error: {e}")
            return []
    
    def _get_default_misconceptions(
        self, 
        error_category: str, 
        learner_answer: str
    ) -> List[Misconception]:
        """Default misconceptions when Course KG is unavailable"""
        if error_category == 'CONCEPTUAL':
            return [Misconception(
                type='unknown_conceptual',
                description='Fundamental misunderstanding detected',
                severity='HIGH',
                confidence=0.6,
                evidence=learner_answer[:100]
            )]
        return []
    
    async def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Cosine similarity between embeddings"""
        if not text1 or not text2:
            return 0.0
        
        if self.embeddings:
            try:
                emb1 = self.embeddings.encode(text1)
                emb2 = self.embeddings.encode(text2)
                
                dot = sum(a * b for a, b in zip(emb1, emb2))
                norm1 = sum(a ** 2 for a in emb1) ** 0.5
                norm2 = sum(a ** 2 for a in emb2) ** 0.5
                
                similarity = dot / (norm1 * norm2 + 1e-8)
                return max(0.0, (similarity + 1) / 2)
            except:
                pass
        
        # Fallback to string similarity
        return self._string_similarity(text1, text2)
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Levenshtein-based similarity"""
        s1_norm = s1.lower().strip()
        s2_norm = s2.lower().strip()
        return SequenceMatcher(None, s1_norm, s2_norm).ratio()
