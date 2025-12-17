"""
Evaluation Data Models for Evaluator Agent.

Per THESIS Section 3.5.4:
- 5 Error Types: CORRECT, CARELESS, INCOMPLETE, PROCEDURAL, CONCEPTUAL
- 5 Path Decisions: MASTERED, PROCEED, ALTERNATE, RETRY, REMEDIATE
- Misconception tracking with severity and frequency
- EvaluationResult with multi-audience feedback
"""

from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass, field


class ErrorType(str, Enum):
    """5 Error Classification Types per THESIS"""
    CORRECT = "CORRECT"           # Score >= 0.95
    CARELESS = "CARELESS"         # Minor typos, arithmetic errors
    INCOMPLETE = "INCOMPLETE"     # Missing parts but correct approach
    PROCEDURAL = "PROCEDURAL"     # Wrong order/syntax but understands concept
    CONCEPTUAL = "CONCEPTUAL"     # Fundamental misunderstanding


class PathDecision(str, Enum):
    """5 Path Decision Types per THESIS Table 3.10"""
    MASTERED = "MASTERED"     # Score >= 0.9, no severe misconceptions
    PROCEED = "PROCEED"       # Score >= 0.8, acceptable understanding
    ALTERNATE = "ALTERNATE"   # Try different example/teaching angle
    RETRY = "RETRY"           # Same concept, new question
    REMEDIATE = "REMEDIATE"   # Go back to prerequisites


@dataclass
class Misconception:
    """
    Misconception detected during evaluation.
    
    Severity levels:
    - LOW: Minor confusion, self-correctable
    - MEDIUM: Needs clarification
    - HIGH: Significant misunderstanding
    - PERSISTENT: Seen 3+ times, requires intervention
    """
    type: str
    description: str
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, PERSISTENT
    confidence: float = 0.7
    evidence: str = ""
    first_seen: datetime = field(default_factory=datetime.now)
    frequency: int = 1
    
    def to_dict(self) -> Dict:
        return {
            'type': self.type,
            'description': self.description,
            'severity': self.severity,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'frequency': self.frequency
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Misconception':
        return cls(
            type=data.get('type', 'unknown'),
            description=data.get('description', ''),
            severity=data.get('severity', 'MEDIUM'),
            confidence=data.get('confidence', 0.7),
            evidence=data.get('evidence', ''),
            frequency=data.get('frequency', 1)
        )


@dataclass
class EvaluationResult:
    """
    Complete evaluation result with multi-audience feedback.
    
    Contains:
    - Scoring data (score, confidence)
    - Error classification
    - Misconceptions detected
    - Mastery tracking
    - Path decision
    - Feedback for 3 audiences (learner, planner, KAG)
    """
    learner_id: str
    concept_id: str
    learner_answer: str
    expected_answer: str
    question_bloom_level: str = "APPLY"
    
    # Scoring
    score: float = 0.0
    confidence: float = 0.0
    
    # Classification
    error_type: ErrorType = ErrorType.CORRECT
    misconceptions: List[Misconception] = field(default_factory=list)
    
    # Mastery
    mastery_before: float = 0.0
    mastery_after: float = 0.0
    attempt_count: int = 1
    
    # Decision
    decision: PathDecision = PathDecision.PROCEED
    
    # Feedback (3 audiences)
    feedback_learner: str = ""
    feedback_planner: Dict = field(default_factory=dict)
    feedback_kag: Dict = field(default_factory=dict)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    evaluation_id: str = ""
    
    def __post_init__(self):
        if not self.evaluation_id:
            import uuid
            self.evaluation_id = f"eval_{uuid.uuid4().hex[:8]}"
    
    def to_dict(self) -> Dict:
        return {
            'evaluation_id': self.evaluation_id,
            'learner_id': self.learner_id,
            'concept_id': self.concept_id,
            'learner_answer': self.learner_answer[:200],  # Truncate for storage
            'expected_answer': self.expected_answer[:200],
            'question_bloom_level': self.question_bloom_level,
            'score': self.score,
            'confidence': self.confidence,
            'error_type': self.error_type.value,
            'misconceptions': [m.to_dict() for m in self.misconceptions],
            'mastery_before': self.mastery_before,
            'mastery_after': self.mastery_after,
            'attempt_count': self.attempt_count,
            'decision': self.decision.value,
            'feedback_learner': self.feedback_learner,
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_event_payload(self) -> Dict:
        """Payload for EVALUATION_COMPLETED event"""
        return {
            'learner_id': self.learner_id,
            'concept_id': self.concept_id,
            'score': self.score,
            'confidence': self.confidence,
            'error_type': self.error_type.value,
            'misconceptions': [m.type for m in self.misconceptions],
            'mastery_before': self.mastery_before,
            'mastery_after': self.mastery_after,
            'decision': self.decision.value,
            'remediation_needed': self.decision == PathDecision.REMEDIATE
        }
    
    @property
    def mastery_gain(self) -> float:
        """M1: Mastery gain metric"""
        return self.mastery_after - self.mastery_before
    
    @property
    def has_severe_misconception(self) -> bool:
        """Check for HIGH or PERSISTENT misconceptions"""
        return any(m.severity in ['HIGH', 'PERSISTENT'] for m in self.misconceptions)
    
    @property
    def has_conceptual_error(self) -> bool:
        """Check for conceptual errors"""
        return self.error_type == ErrorType.CONCEPTUAL or \
               any('conceptual' in m.type.lower() for m in self.misconceptions)
