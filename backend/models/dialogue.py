"""
Dialogue State Machine for Tutor Agent.

Per THESIS Section 3.5.x:
- 4 phases: EXPLANATION → QUESTIONING → PRACTICE → ASSESSMENT
- State transitions based on turns and correct answers
- Scaffolding levels: HIGH → MEDIUM → LOW
"""

from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict


class DialoguePhase(str, Enum):
    """4-phase dialogue state machine per THESIS"""
    EXPLANATION = "EXPLANATION"     # Introduce concept
    QUESTIONING = "QUESTIONING"     # Probe understanding
    PRACTICE = "PRACTICE"           # Apply knowledge
    ASSESSMENT = "ASSESSMENT"       # Evaluate mastery


class ScaffoldingLevel(str, Enum):
    """Scaffolding reduction levels"""
    HIGH = "HIGH"       # Maximum support
    MEDIUM = "MEDIUM"   # Moderate support
    LOW = "LOW"         # Minimal support


class DialogueState:
    """
    Stateful dialogue tracking for Socratic tutoring.
    
    Phase advancement triggers (per handoff doc):
    - EXPLANATION (2+ turns) → QUESTIONING
    - QUESTIONING (2+ correct OR 3+ attempts) → PRACTICE
    - PRACTICE (3+ attempts) → ASSESSMENT → Handoff to Evaluator
    """
    
    def __init__(self, learner_id: str, concept_id: str, learning_style: str = "VISUAL"):
        self.learner_id = learner_id
        self.concept_id = concept_id
        self.learning_style = learning_style
        
        # Phase tracking
        self.phase = DialoguePhase.EXPLANATION
        self.scaffolding_level = ScaffoldingLevel.HIGH
        
        # Turn tracking
        self.turn_count = 0
        self.attempts_in_phase = 0
        self.correct_answers = 0
        
        # Content tracking
        self.last_user_response = ""
        self.interaction_log: List[Dict] = []
        self.suspected_misconceptions: List[Dict] = []
        self.hints_given: List[str] = []
        
        # Timestamps
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def advance_phase(self):
        """Move to next phase in state machine"""
        phases = [
            DialoguePhase.EXPLANATION, 
            DialoguePhase.QUESTIONING, 
            DialoguePhase.PRACTICE, 
            DialoguePhase.ASSESSMENT
        ]
        idx = phases.index(self.phase)
        if idx < len(phases) - 1:
            self.phase = phases[idx + 1]
            self.attempts_in_phase = 0
            self.correct_answers = 0
            self.last_updated = datetime.now()
    
    def reduce_scaffolding(self):
        """Reduce support level as learner progresses"""
        if self.scaffolding_level == ScaffoldingLevel.HIGH:
            self.scaffolding_level = ScaffoldingLevel.MEDIUM
        elif self.scaffolding_level == ScaffoldingLevel.MEDIUM:
            self.scaffolding_level = ScaffoldingLevel.LOW
    
    def should_advance_phase(self) -> bool:
        """
        Check if phase should advance based on triggers.
        
        Per handoff doc:
        - EXPLANATION: 2+ turns
        - QUESTIONING: 2+ correct OR 3+ attempts
        - PRACTICE: 3+ attempts
        """
        if self.phase == DialoguePhase.EXPLANATION:
            return self.turn_count >= 2
        elif self.phase == DialoguePhase.QUESTIONING:
            return self.correct_answers >= 2 or self.attempts_in_phase >= 3
        elif self.phase == DialoguePhase.PRACTICE:
            return self.attempts_in_phase >= 3
        return False
    
    def record_turn(self, user_message: str, tutor_response: str, is_correct: bool = False):
        """Record a dialogue turn"""
        self.turn_count += 1
        self.attempts_in_phase += 1
        self.last_user_response = user_message
        self.last_updated = datetime.now()
        
        if is_correct:
            self.correct_answers += 1
        
        self.interaction_log.append({
            'role': 'LEARNER',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        self.interaction_log.append({
            'role': 'TUTOR',
            'content': tutor_response,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_misconception(self, misconception_type: str, confidence: float, evidence: str):
        """Track detected misconception"""
        self.suspected_misconceptions.append({
            'type': misconception_type,
            'confidence': confidence,
            'evidence': evidence,
            'detected_at': datetime.now().isoformat(),
            'phase': self.phase.value
        })
    
    def to_dict(self) -> Dict:
        """Serialize state for storage"""
        return {
            'learner_id': self.learner_id,
            'concept_id': self.concept_id,
            'learning_style': self.learning_style,
            'phase': self.phase.value,
            'scaffolding_level': self.scaffolding_level.value,
            'turn_count': self.turn_count,
            'attempts_in_phase': self.attempts_in_phase,
            'correct_answers': self.correct_answers,
            'interaction_log': self.interaction_log,
            'suspected_misconceptions': self.suspected_misconceptions,
            'hints_given': self.hints_given,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DialogueState':
        """Deserialize state from storage"""
        state = cls(
            learner_id=data['learner_id'],
            concept_id=data['concept_id'],
            learning_style=data.get('learning_style', 'VISUAL')
        )
        state.phase = DialoguePhase(data['phase'])
        state.scaffolding_level = ScaffoldingLevel(data.get('scaffolding_level', 'HIGH'))
        state.turn_count = data.get('turn_count', 0)
        state.attempts_in_phase = data.get('attempts_in_phase', 0)
        state.correct_answers = data.get('correct_answers', 0)
        state.interaction_log = data.get('interaction_log', [])
        state.suspected_misconceptions = data.get('suspected_misconceptions', [])
        state.hints_given = data.get('hints_given', [])
        return state
