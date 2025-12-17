"""
Harvard 7 Principles Enforcer for Tutor Agent.

Per THESIS Section 3.5.x, implements:
1. Active Learning - NO direct answers, YES probing questions
2. Cognitive Load - MAX 2-4 sentences (5-6 for ASSESSMENT)
3. One Step at a Time - Wait before next reveal
4. Personalization - Reference learning style
5. Self-Thinking - Probing: "Why?", "What if?", "Can you?"
6. Growth Mindset - "Good attempt!" NOT "That's wrong"
7. Personalized Feedback - Address specific misconceptions
"""

import logging
import re
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class Harvard7Enforcer:
    """
    Enforce Harvard 7 Principles on tutor responses.
    
    Purpose: Ensure pedagogically sound responses that promote
    active learning and minimize cognitive overload.
    """
    
    # Cognitive load limits (sentences)
    MAX_SENTENCES_NORMAL = 4
    MAX_SENTENCES_ASSESSMENT = 6
    
    # Direct answer patterns to remove
    DIRECT_ANSWER_PATTERNS = [
        r"the answer is",
        r"the correct answer",
        r"you should know that",
        r"the solution is",
        r"here's the answer",
        r"simply put,? it is"
    ]
    
    # Growth mindset replacements
    GROWTH_MINDSET_REPLACEMENTS = {
        "wrong": "interesting attempt - let's think differently",
        "incorrect": "great effort! Let's refine",
        "mistake": "learning opportunity",
        "failed": "made progress toward",
        "don't understand": "are still exploring",
        "can't": "are learning to"
    }
    
    # Probing question templates
    PROBING_QUESTIONS = [
        "Why do you think that?",
        "What would happen if...?",
        "Can you think of an example?",
        "How does this connect to what we learned before?",
        "What's your reasoning here?"
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.Harvard7Enforcer")
    
    def enforce(
        self, 
        response: str, 
        learner_context: Dict, 
        phase: str, 
        misconception: Optional[Dict] = None
    ) -> str:
        """
        Apply all 7 Harvard principles to response.
        
        Args:
            response: Raw LLM response
            learner_context: {learning_style, mastery_level, etc}
            phase: Current dialogue phase
            misconception: Detected misconception if any
        
        Returns:
            Enforced response
        """
        enforced = response
        
        # 1. Remove direct answers (Active Learning)
        enforced = self._remove_direct_answers(enforced)
        
        # 2. Limit cognitive load
        enforced = self._limit_cognitive_load(enforced, phase)
        
        # 3. Add probing questions (Self-Thinking)
        enforced = self._add_probing_questions(enforced)
        
        # 4. Apply growth mindset language
        enforced = self._add_growth_mindset_language(enforced)
        
        # 5. Personalize to learning style
        learning_style = learner_context.get('learning_style', 'VISUAL')
        enforced = self._personalize_to_style(enforced, learning_style)
        
        # 6. Address misconception if detected
        if misconception:
            enforced = self._address_misconception(enforced, misconception)
        
        return enforced.strip()
    
    def _remove_direct_answers(self, response: str) -> str:
        """
        Principle 1: Active Learning
        Replace direct answers with guiding prompts.
        """
        result = response
        
        for pattern in self.DIRECT_ANSWER_PATTERNS:
            # Case-insensitive replacement
            result = re.sub(
                pattern, 
                "Let's think about this -", 
                result, 
                flags=re.IGNORECASE
            )
        
        return result
    
    def _limit_cognitive_load(self, response: str, phase: str) -> str:
        """
        Principle 2: Cognitive Load
        Limit to 2-4 sentences (5-6 for ASSESSMENT).
        """
        max_sentences = (
            self.MAX_SENTENCES_ASSESSMENT 
            if phase == 'ASSESSMENT' 
            else self.MAX_SENTENCES_NORMAL
        )
        
        # Split by sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', response)
        
        if len(sentences) > max_sentences:
            sentences = sentences[:max_sentences]
            # Ensure proper ending
            result = ' '.join(sentences)
            if not result.endswith(('.', '!', '?')):
                result += '.'
            return result
        
        return response
    
    def _add_probing_questions(self, response: str) -> str:
        """
        Principle 5: Self-Thinking
        Ensure response includes a probing question.
        """
        if '?' not in response:
            # Add a contextual probing question
            import random
            question = random.choice(self.PROBING_QUESTIONS[:3])
            response = f"{response}\n\n{question}"
        
        return response
    
    def _add_growth_mindset_language(self, response: str) -> str:
        """
        Principle 6: Growth Mindset
        Replace negative language with growth-oriented alternatives.
        """
        result = response
        
        for negative, positive in self.GROWTH_MINDSET_REPLACEMENTS.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(negative), re.IGNORECASE)
            result = pattern.sub(positive, result)
        
        return result
    
    def _personalize_to_style(self, response: str, learning_style: str) -> str:
        """
        Principle 4: Personalization
        Adapt language to learner's preferred style.
        """
        if learning_style == 'VISUAL':
            response = response.replace('think about', 'picture in your mind')
            response = response.replace('consider', 'visualize')
        elif learning_style == 'AUDITORY':
            response = response.replace('look at', 'listen to how')
            response = response.replace('see', 'hear')
        elif learning_style == 'KINESTHETIC':
            response = response.replace('understand', 'try working through')
            response = response.replace('think about', 'hands-on with')
        elif learning_style == 'READING':
            response = response.replace('picture', 'read about')
        
        return response
    
    def _address_misconception(self, response: str, misconception: Dict) -> str:
        """
        Principle 7: Personalized Feedback
        Address specific misconception without being negative.
        """
        misconception_type = misconception.get('type', 'unknown')
        
        # Add gentle clarification
        clarification = (
            f"\n\nI noticed something interesting in your thinking about "
            f"{misconception_type}. Let's explore that together."
        )
        
        return response + clarification
    
    def validate_response(self, response: str, phase: str) -> Dict:
        """
        Validate that response follows Harvard 7 principles.
        
        Returns:
            {
                'is_valid': bool,
                'violations': List[str],
                'suggestions': List[str]
            }
        """
        violations = []
        suggestions = []
        
        # Check for direct answers
        for pattern in self.DIRECT_ANSWER_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append("Contains direct answer")
                suggestions.append("Replace with guiding prompt")
                break
        
        # Check cognitive load
        sentences = re.split(r'(?<=[.!?])\s+', response)
        max_allowed = (
            self.MAX_SENTENCES_ASSESSMENT 
            if phase == 'ASSESSMENT' 
            else self.MAX_SENTENCES_NORMAL
        )
        if len(sentences) > max_allowed:
            violations.append(f"Too many sentences ({len(sentences)} > {max_allowed})")
            suggestions.append("Reduce to fewer sentences")
        
        # Check for probing question
        if '?' not in response:
            violations.append("Missing probing question")
            suggestions.append("Add a question like 'Why do you think that?'")
        
        # Check for negative language
        for negative in self.GROWTH_MINDSET_REPLACEMENTS:
            if negative.lower() in response.lower():
                violations.append(f"Contains negative language: '{negative}'")
                suggestions.append(f"Replace with: '{self.GROWTH_MINDSET_REPLACEMENTS[negative]}'")
        
        return {
            'is_valid': len(violations) == 0,
            'violations': violations,
            'suggestions': suggestions
        }
