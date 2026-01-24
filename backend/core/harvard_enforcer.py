from enum import Enum
from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

class HarvardPrinciple(Enum):
    ACTIVE_LEARNING = "active_learning"
    COGNITIVE_LOAD = "cognitive_load"
    SCAFFOLDING = "scaffolding"
    REFLECTION = "reflection"
    GROWTH_MINDSET = "growth_mindset"
    PERSONALIZED_FEEDBACK = "personalized_feedback"
    MISCONCEPTION_HANDLING = "misconception_handling"

class Harvard7Enforcer:
    """
    Enforces all 7 Harvard pedagogical principles in LLM-generated responses.
    
    Based on: Kestin et al. (2025), "AI tutoring outperforms in-class active learning"
    
    PRINCIPLES:
    1. Encourage active learning (student does cognitive work)
    2. Manage cognitive load (avoid overwhelming)
    3. Go step-by-step (scaffolding)
    4. Encourage reflection (thinking, not answers)
    5. Cultivate growth mindset (effort → improvement)
    6. Give personalized feedback (specific to student state)
    7. Manage misconceptions (address specific errors)
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.enforcement_scores = {}
    
    def enforce_all_principles(
        self,
        response: str,
        learner_profile: Dict[str, Any],
        recent_error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Apply all 7 enforcements to a response.
        
        Returns:
            {
                "response": str (improved response),
                "violations": [str] (which principles were violated),
                "score": float (0-1, how well enforced)
            }
        """
        enforced = response
        violations = []
        
        # Apply each principle in order
        enforced, v1 = self._enforce_active_learning(enforced, learner_profile)
        violations.extend(v1)
        
        enforced, v2 = self._enforce_cognitive_load(enforced, learner_profile)
        violations.extend(v2)
        
        enforced, v3 = self._enforce_scaffolding(enforced, learner_profile)
        violations.extend(v3)
        
        enforced, v4 = self._enforce_reflection(enforced)
        violations.extend(v4)
        
        enforced, v5 = self._enforce_growth_mindset(enforced)
        violations.extend(v5)
        
        enforced, v6 = self._enforce_personalized_feedback(enforced, learner_profile)
        violations.extend(v6)
        
        if recent_error:
            enforced, v7 = self._enforce_misconception_handling(enforced, recent_error, learner_profile)
            violations.extend(v7)
        
        # Compute compliance score
        max_violations = 7
        compliance_score = 1.0 - (len(violations) / max_violations)
        
        logger.debug(f"Harvard 7 Score: {compliance_score:.2f} ({7-len(violations)}/7 principles satisfied)")
        
        return {
            "response": enforced,
            "violations": violations,
            "score": compliance_score,
            "enforced_principles": 7 - len(violations)
        }
    
    def _enforce_active_learning(self, response: str, profile: Dict) -> tuple:
        """
        Principle 1: Encourage active learning
        
        CHECK: Response contains at least one question OR asks learner to do work
        ACTION: If not, insert a question
        """
        violations = []
        
        # Heuristic 1: Does response have a question mark?
        has_question = "?" in response
        
        # Heuristic 2: Does it ask learner to do something? (verb: calculate, identify, think, try, etc.)
        action_verbs = ["calculate", "identify", "think", "try", "determine", "solve", "predict", "analyze"]
        has_action = any(verb in response.lower() for verb in action_verbs)
        
        if not (has_question or has_action):
            violations.append("ACTIVE_LEARNING")
            # Insert a question
            response += "\n\nNow, try to [action] on your own. What do you think?"
        
        return response, violations
    
    def _enforce_cognitive_load(self, response: str, profile: Dict) -> tuple:
        """
        Principle 2: Manage cognitive load
        
        CHECK: Response length, complexity level
        - If high mastery learner: OK to be longer/complex
        - If low mastery learner: should be concise
        ACTION: Adjust verbosity, break into substeps
        """
        violations = []
        mastery_level = profile.get("overall_mastery", 0.5)
        
        # Max length guidelines (words)
        max_words_low = 150
        max_words_medium = 300
        max_words_high = 500
        
        word_count = len(response.split())
        
        if mastery_level < 0.3:  # Low mastery
            max_words = max_words_low
        elif mastery_level < 0.7:  # Medium
            max_words = max_words_medium
        else:  # High
            max_words = max_words_high
        
        if word_count > max_words:
            violations.append("COGNITIVE_LOAD")
            # Truncate and simplify
            sentences = response.split(". ")
            response = ". ".join(sentences[: max(2, len(sentences) // 2)]) + "."
        
        # Check for overwhelming complexity (e.g., too many technical terms)
        complex_terms = len(re.findall(r"\b[A-Z][a-z]+[A-Z][a-z]+\b", response))  # CamelCase
        if complex_terms > 5:
            violations.append("COGNITIVE_LOAD")
            # Note: Could auto-simplify, but risky
        
        return response, violations
    
    def _enforce_scaffolding(self, response: str, profile: Dict) -> tuple:
        """
        Principle 3: Go step-by-step (scaffolding)
        
        CHECK: Response has clear step progression
        ACTION: If not, restructure into numbered steps
        """
        violations = []
        
        # Heuristic: Does response have numbered/bulleted steps?
        has_steps = bool(re.search(r"(^|\n)[\d\-\*]\.", response, re.MULTILINE))
        
        if not has_steps:
            violations.append("SCAFFOLDING")
            # Restructure response into steps
            # This is simplified; real version would use LLM to restructure
            lines = response.split(". ")
            if len(lines) > 1:
                response = "\n".join(f"{i+1}. {line}" for i, line in enumerate(lines[:5]))
        
        return response, violations
    
    def _enforce_reflection(self, response: str) -> tuple:
        """
        Principle 4: Encourage reflection
        
        CHECK: Response encourages learner to think, not just gives answer
        ACTION: Ask reflective questions like "Why?" "How?" "What do you notice?"
        """
        violations = []
        
        # Heuristic: Does response ask learner to think/reflect?
        reflection_words = ["Why", "How", "What do you notice", "What would happen", "Think about"]
        has_reflection = any(word in response for word in reflection_words)
        
        if not has_reflection:
            violations.append("REFLECTION")
            response += "\n\nWhat do you notice about [key insight]? Why might that be?"
        
        return response, violations
    
    def _enforce_growth_mindset(self, response: str) -> tuple:
        """
        Principle 5: Cultivate growth mindset
        
        CHECK: Response emphasizes effort, learning, improvement (not innate ability)
        ACTION: Replace fixed mindset language with growth mindset language
        """
        violations = []
        
        # Fixed mindset phrases to replace
        fixed_phrases = {
            "you can't": "you haven't learned how to yet",
            "you're not good at": "you're developing skill in",
            "it's too hard": "it's challenging, which helps you learn",
            "you'll never": "with practice, you can",
        }
        
        original = response
        for fixed, growth in fixed_phrases.items():
            response = re.sub(fixed, growth, response, flags=re.IGNORECASE)
        
        if response != original:
            # Replaced at least one phrase
            pass
        else:
            # Check if response mentions effort/improvement/learning
            growth_words = ["effort", "practice", "learn", "improve", "progress", "develop"]
            has_growth = any(word in response.lower() for word in growth_words)
            
            if not has_growth:
                violations.append("GROWTH_MINDSET")
                response += "\n\nWith continued practice and effort, you'll improve on this concept."
        
        return response, violations
    
    def _enforce_personalized_feedback(self, response: str, profile: Dict) -> tuple:
        """
        Principle 6: Give personalized feedback
        
        CHECK: Response addresses learner's specific context/errors
        ACTION: Ensure feedback isn't generic
        """
        violations = []
        
        # Heuristic: Does response include learner-specific info?
        # (This is hard to check without the original query context)
        # For now, just check if it's not too generic
        
        generic_phrases = ["in general", "typically", "usually", "for most people"]
        too_generic = sum(1 for phrase in generic_phrases if phrase in response.lower())
        
        # Some generic OK, but shouldn't dominate
        if too_generic > 2:
            violations.append("PERSONALIZED_FEEDBACK")
        
        return response, violations
    
    def _enforce_misconception_handling(
        self,
        response: str,
        error_type: str,
        profile: Dict
    ) -> tuple:
        """
        Principle 7: Manage misconceptions
        
        CHECK: Response directly addresses the learner's specific error
        ACTION: Provide targeted correction + explanation
        
        Args:
            error_type: e.g., "CONCEPTUAL", "COMPUTATIONAL", "PROCEDURAL"
        """
        violations = []
        
        if error_type == "CONCEPTUAL":
            # Should explain core concept, not just method
            if "concept" not in response.lower() and "definition" not in response.lower():
                violations.append("MISCONCEPTION_HANDLING")
                response = f"I notice a conceptual confusion. Let me clarify:\n\n{response}"
        
        elif error_type == "COMPUTATIONAL":
            # Should show correct calculation step-by-step
            if "step" not in response.lower() and "=" not in response:
                violations.append("MISCONCEPTION_HANDLING")
                response = f"Let me show you the correct steps:\n\n{response}"
        
        elif error_type == "PROCEDURAL":
            # Should explain correct method
            if "method" not in response.lower() and "process" not in response.lower():
                violations.append("MISCONCEPTION_HANDLING")
                response = f"Here's the correct procedure:\n\n{response}"
        
        return response, violations
    
    # ============ TESTING ============
    
    def test_harvard7_score(self, response: str, learner_profile: Dict):
        """Run all 7 checks on a response"""
        result = self.enforce_all_principles(response, learner_profile)
        logger.info(f"Harvard 7 Compliance Score: {result['score']:.2f}/1.0")
        if result['violations']:
            logger.warning(f"Violations: {', '.join(result['violations'])}")
        return result
