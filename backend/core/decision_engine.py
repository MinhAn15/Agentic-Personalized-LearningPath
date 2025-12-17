"""
Decision Engine for Evaluator Agent.

Per THESIS Section 3.5.4 Table 3.10:
- 5 path decisions: MASTERED, PROCEED, ALTERNATE, RETRY, REMEDIATE
- Based on mastery level, error type, and misconceptions
"""

import logging
from typing import List

from backend.models.evaluation import PathDecision, ErrorType, Misconception

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Decide next learning path action based on evaluation results.
    
    Decision Matrix (THESIS Table 3.10):
    ─────────────────────────────────────────────────────────────────
    mastery   │ misconceptions │ decision    │ reasoning
    ─────────────────────────────────────────────────────────────────
    ≥ 0.90    │ None/Low       │ MASTERED    │ Perfect, skip ahead
    0.80-0.89 │ None           │ PROCEED     │ Good enough, move next
    0.60-0.79 │ Careless       │ PROCEED     │ Acceptable with caution
    0.60-0.79 │ Conceptual     │ ALTERNATE   │ Try different approach
    0.40-0.59 │ Any            │ REMEDIATE   │ Struggling, go backward
    < 0.40    │ Any            │ REMEDIATE   │ Fundamental gap
    """
    
    def __init__(self, personal_kg=None):
        self.personal_kg = personal_kg
        self.logger = logging.getLogger(f"{__name__}.DecisionEngine")
    
    async def decide(
        self, 
        mastery_new: float, 
        error_type: ErrorType,
        misconceptions: List[Misconception], 
        learner_id: str, 
        concept_id: str
    ) -> PathDecision:
        """
        Decide next action based on mastery and misconceptions.
        
        Returns:
            PathDecision (MASTERED, PROCEED, ALTERNATE, RETRY, REMEDIATE)
        """
        # Analyze misconceptions
        has_severe = any(m.severity in ['HIGH', 'PERSISTENT'] for m in misconceptions)
        has_conceptual = any(
            'conceptual' in m.type.lower() or m.severity == 'HIGH' 
            for m in misconceptions
        )
        has_persistent = any(m.frequency >= 3 for m in misconceptions)
        
        # Check for learning style mismatch (if Personal KG available)
        personal_mismatch = await self._detect_style_mismatch(learner_id, concept_id)
        
        # Decision tree per THESIS Table 3.10
        if mastery_new >= 0.9 and not has_severe:
            decision = PathDecision.MASTERED
        
        elif mastery_new >= 0.8 and not has_conceptual:
            decision = PathDecision.PROCEED
        
        elif mastery_new >= 0.6 and error_type == ErrorType.CARELESS:
            decision = PathDecision.PROCEED
        
        elif mastery_new >= 0.6 and has_conceptual:
            if personal_mismatch:
                decision = PathDecision.ALTERNATE
            else:
                decision = PathDecision.RETRY
        
        elif mastery_new < 0.6 and (has_persistent or has_conceptual):
            decision = PathDecision.REMEDIATE
        
        elif mastery_new < 0.4:
            decision = PathDecision.REMEDIATE
        
        else:
            decision = PathDecision.RETRY
        
        self.logger.info(
            f"Decision for {learner_id}/{concept_id}: {decision.value} "
            f"(mastery={mastery_new:.2f}, error={error_type.value})"
        )
        
        return decision
    
    async def _detect_style_mismatch(
        self, 
        learner_id: str, 
        concept_id: str
    ) -> bool:
        """Check if learning style doesn't match content delivery"""
        if not self.personal_kg:
            return False
        
        try:
            if hasattr(self.personal_kg, 'detect_style_mismatch'):
                return await self.personal_kg.detect_style_mismatch(learner_id, concept_id)
            
            # Check if multiple failures with same content type
            if hasattr(self.personal_kg, 'get_failure_history'):
                failures = await self.personal_kg.get_failure_history(learner_id, concept_id)
                if failures and len(failures) >= 2:
                    # Same content type failed multiple times
                    content_types = [f.get('content_type') for f in failures]
                    if len(set(content_types)) == 1:
                        return True
            
            return False
        except:
            return False
    
    def get_remediation_reason(
        self, 
        decision: PathDecision,
        misconceptions: List[Misconception]
    ) -> str:
        """Explain why remediation is needed"""
        if decision == PathDecision.REMEDIATE:
            if misconceptions:
                primary = misconceptions[0]
                if primary.frequency >= 3:
                    return f"Persistent misconception: {primary.type}. Requires prerequisite review."
                else:
                    return f"Misconception detected: {primary.type}. Reviewing fundamentals."
            else:
                return "Fundamental gap detected. Reviewing prerequisites."
        
        elif decision == PathDecision.ALTERNATE:
            return "Current approach not working. Trying different teaching angle."
        
        elif decision == PathDecision.RETRY:
            return "Minor issues. Same concept with new question."
        
        return ""
    
    def get_decision_metadata(
        self, 
        decision: PathDecision,
        mastery: float,
        misconceptions: List[Misconception]
    ) -> dict:
        """Get metadata for Path Planner"""
        suggestions = {
            PathDecision.MASTERED: 'Ready to skip ahead to advanced topics',
            PathDecision.PROCEED: 'Can move to next concept',
            PathDecision.ALTERNATE: 'Try different example or teaching angle',
            PathDecision.RETRY: 'Same concept, new question',
            PathDecision.REMEDIATE: 'Must go back to prerequisites'
        }
        
        return {
            'decision': decision.value,
            'suggestion': suggestions.get(decision, 'Continue learning'),
            'confidence': min(1.0, mastery + 0.1) if decision in [PathDecision.MASTERED, PathDecision.PROCEED] else 0.6,
            'requires_replanning': decision in [PathDecision.ALTERNATE, PathDecision.REMEDIATE],
            'misconception_types': [m.type for m in misconceptions]
        }
