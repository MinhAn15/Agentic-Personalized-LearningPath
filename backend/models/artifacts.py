"""
Artifact Data Models for KAG Agent.

Per THESIS Section 3.5.5:
- 4 artifact types: ATOMIC_NOTE, MISCONCEPTION_NOTE, SUMMARY_NOTE, CONCEPT_MAP
- Zettelkasten methodology: atomicity, own words, contextualization, linking
"""

import uuid
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass, field


class ArtifactType(str, Enum):
    """Zettelkasten Artifact Types"""
    ATOMIC_NOTE = "ATOMIC_NOTE"               # Single learning insight
    MISCONCEPTION_NOTE = "MISCONCEPTION_NOTE" # Document common error
    SUMMARY_NOTE = "SUMMARY_NOTE"             # Session synthesis
    CONCEPT_MAP = "CONCEPT_MAP"               # Visual relationship graph


@dataclass
class AtomicNote:
    """
    Zettelkasten atomic note following 4 principles:
    1. Atomicity - One note = One key insight
    2. Own Words - Written in learner's terms
    3. Contextualization - What is this useful for?
    4. Linking - Connected to related notes
    """
    learner_id: str
    concept_id: str
    note_type: ArtifactType = ArtifactType.ATOMIC_NOTE
    
    # Identity
    note_id: str = field(default_factory=lambda: f"note_{uuid.uuid4().hex[:8]}")
    
    # Content (Zettelkasten structure)
    title: str = ""
    key_insight: str = ""        # Core understanding in 1 sentence
    personal_example: str = ""   # Concrete illustration
    common_mistake: str = ""     # What to avoid
    content: str = ""            # Full formatted note
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)  # Related concept_ids
    
    # Provenance
    source_eval_id: Optional[str] = None
    source_session_id: Optional[str] = None
    
    # Timestamps & Review
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    review_count: int = 0
    last_reviewed: Optional[datetime] = None
    
    def __post_init__(self):
        """Generate note_id if not provided"""
        if not self.note_id or self.note_id.startswith("note_"):
            self.note_id = f"{self.learner_id}.note.{uuid.uuid4().hex[:8]}"
    
    def to_dict(self) -> Dict:
        return {
            'note_id': self.note_id,
            'learner_id': self.learner_id,
            'concept_id': self.concept_id,
            'type': self.note_type.value,
            'title': self.title,
            'key_insight': self.key_insight,
            'personal_example': self.personal_example,
            'common_mistake': self.common_mistake,
            'content': self.content,
            'tags': self.tags,
            'connections': self.connections,
            'source_eval_id': self.source_eval_id,
            'source_session_id': self.source_session_id,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'review_count': self.review_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AtomicNote':
        note = cls(
            learner_id=data['learner_id'],
            concept_id=data['concept_id'],
            note_type=ArtifactType(data.get('type', 'ATOMIC_NOTE'))
        )
        note.note_id = data.get('note_id', note.note_id)
        note.title = data.get('title', '')
        note.key_insight = data.get('key_insight', '')
        note.personal_example = data.get('personal_example', '')
        note.common_mistake = data.get('common_mistake', '')
        note.content = data.get('content', '')
        note.tags = data.get('tags', [])
        note.connections = data.get('connections', [])
        note.source_eval_id = data.get('source_eval_id')
        note.source_session_id = data.get('source_session_id')
        note.review_count = data.get('review_count', 0)
        return note


@dataclass
class MisconceptionNote(AtomicNote):
    """
    Specialized note for documenting learning misconceptions.
    
    Triggered when: score < 0.5 AND conceptual error detected
    Purpose: Track and address persistent misunderstandings
    """
    misconception_type: str = ""
    error_frequency: int = 1
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, PERSISTENT
    remediation_concepts: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        self.note_type = ArtifactType.MISCONCEPTION_NOTE
    
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'misconception_type': self.misconception_type,
            'error_frequency': self.error_frequency,
            'severity': self.severity,
            'remediation_concepts': self.remediation_concepts
        })
        return data


@dataclass
class SummaryNote(AtomicNote):
    """
    Session summary synthesizing multiple concepts.
    
    Triggered when: End of session with 3+ concepts covered
    """
    concepts_covered: List[str] = field(default_factory=list)
    session_duration_minutes: int = 0
    overall_mastery: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        self.note_type = ArtifactType.SUMMARY_NOTE
    
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'concepts_covered': self.concepts_covered,
            'session_duration_minutes': self.session_duration_minutes,
            'overall_mastery': self.overall_mastery
        })
        return data


@dataclass
class ArtifactState:
    """
    Track artifact generation state per learner.
    
    Stored in Central State for analytics and PKM queries.
    """
    learner_id: str
    created_artifact_ids: List[str] = field(default_factory=list)
    recent_artifacts: List[Dict] = field(default_factory=list)  # Last 10
    artifact_count_by_type: Dict[str, int] = field(default_factory=dict)
    total_words_created: int = 0
    last_artifact_created: Optional[str] = None
    
    def __post_init__(self):
        if not self.artifact_count_by_type:
            self.artifact_count_by_type = {t.value: 0 for t in ArtifactType}
    
    def add_artifact(self, artifact: AtomicNote):
        """Track new artifact creation"""
        self.created_artifact_ids.append(artifact.note_id)
        
        # Update recent artifacts (keep last 10)
        self.recent_artifacts.append({
            'note_id': artifact.note_id,
            'type': artifact.note_type.value,
            'concept_id': artifact.concept_id,
            'title': artifact.title[:50],
            'created_at': artifact.created_at.isoformat()
        })
        if len(self.recent_artifacts) > 10:
            self.recent_artifacts = self.recent_artifacts[-10:]
        
        # Update counts
        self.artifact_count_by_type[artifact.note_type.value] = \
            self.artifact_count_by_type.get(artifact.note_type.value, 0) + 1
        
        # Update stats
        self.total_words_created += len(artifact.content.split())
        self.last_artifact_created = artifact.created_at.isoformat()
    
    def to_dict(self) -> Dict:
        return {
            'learner_id': self.learner_id,
            'artifact_ids': self.created_artifact_ids,
            'recent_artifacts': self.recent_artifacts,
            'counts_by_type': self.artifact_count_by_type,
            'total_words': self.total_words_created,
            'last_created': self.last_artifact_created
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ArtifactState':
        state = cls(learner_id=data['learner_id'])
        state.created_artifact_ids = data.get('artifact_ids', [])
        state.recent_artifacts = data.get('recent_artifacts', [])
        state.artifact_count_by_type = data.get('counts_by_type', {})
        state.total_words_created = data.get('total_words', 0)
        state.last_artifact_created = data.get('last_created')
        return state
