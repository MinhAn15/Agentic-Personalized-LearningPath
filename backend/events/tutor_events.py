"""
Event schemas for Tutor Agent.

Per THESIS Section 3.5.x:
- TUTOR_GUIDANCE_PROVIDED: Sent after each response
- TUTOR_ASSESSMENT_READY: Handoff to Evaluator
- TUTOR_MISCONCEPTION_DETECTED: Alert for tracking
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List


class TutorEventType(str, Enum):
    """Tutor Agent event types"""
    GUIDANCE_PROVIDED = "TUTOR_GUIDANCE_PROVIDED"
    ASSESSMENT_READY = "TUTOR_ASSESSMENT_READY"
    MISCONCEPTION_DETECTED = "TUTOR_MISCONCEPTION_DETECTED"


def create_guidance_event(
    learner_id: str, 
    concept_id: str, 
    phase: str, 
    confidence: float, 
    response_text: str
) -> Dict:
    """Create TUTOR_GUIDANCE_PROVIDED event"""
    return {
        'event_type': TutorEventType.GUIDANCE_PROVIDED.value,
        'timestamp': datetime.now().isoformat(),
        'learner_id': learner_id,
        'concept_id': concept_id,
        'phase': phase,
        'confidence': confidence,
        'response_preview': response_text[:200] if response_text else ''
    }


def create_assessment_ready_event(
    learner_id: str, 
    concept_id: str, 
    transcript: List[Dict], 
    misconceptions: List[Dict]
) -> Dict:
    """
    Create TUTOR_ASSESSMENT_READY event for Evaluator handoff.
    
    This event signals Agent 5 (Evaluator) to begin formal assessment.
    """
    return {
        'event_type': TutorEventType.ASSESSMENT_READY.value,
        'timestamp': datetime.now().isoformat(),
        'learner_id': learner_id,
        'concept_id': concept_id,
        'dialogue_transcript': transcript,
        'suspected_misconceptions': misconceptions,
        'total_turns': len(transcript) // 2
    }


def create_misconception_detected_event(
    learner_id: str,
    concept_id: str,
    misconception_type: str,
    confidence: float,
    evidence: str
) -> Dict:
    """Create TUTOR_MISCONCEPTION_DETECTED event"""
    return {
        'event_type': TutorEventType.MISCONCEPTION_DETECTED.value,
        'timestamp': datetime.now().isoformat(),
        'learner_id': learner_id,
        'concept_id': concept_id,
        'misconception': {
            'type': misconception_type,
            'confidence': confidence,
            'evidence': evidence
        }
    }
