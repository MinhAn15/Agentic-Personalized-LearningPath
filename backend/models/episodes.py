# Episodic Memory Models
"""
Episodic Memory for Learner Profile (per THESIS Section 3.5.1.3).

4 Episode Types:
1. SESSION: Track learning sessions
2. CONCEPT: Track concept interactions
3. ERROR: Track misconceptions
4. ARTIFACT: Track generated notes

Storage: Neo4j Personal KG (Layer 3)
Schema: Learner --HAS_SESSION--> SessionEpisode --COVERS_CONCEPT--> ConceptEpisode
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class EpisodeType(str, Enum):
    """4 types of episodic memory"""
    SESSION = "SESSION"      # Track learning sessions
    CONCEPT = "CONCEPT"      # Track concept interactions
    ERROR = "ERROR"          # Track misconceptions
    ARTIFACT = "ARTIFACT"    # Track generated notes


class Episode(BaseModel):
    """Base episode class"""
    episode_id: str
    episode_type: EpisodeType
    timestamp: datetime = Field(default_factory=datetime.now)
    learner_id: str
    concept_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class SessionEpisode(Episode):
    """
    Track learning session.
    
    Neo4j: (Learner)-[:HAS_SESSION]->(SessionEpisode)
    """
    episode_type: EpisodeType = EpisodeType.SESSION
    session_id: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "ACTIVE"  # ACTIVE, COMPLETED, ABANDONED
    
    # Session content
    concepts_covered: List[str] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    # [{type: "CONCEPT_STARTED", time: ..., concept_id: ...}, ...]
    
    # Final state
    final_state: Dict[str, Any] = Field(default_factory=lambda: {
        "concepts_completed": 0,
        "skills_gained": [],
        "total_duration_minutes": 0
    })
    
    def add_event(self, event_type: str, concept_id: str = None, **kwargs):
        """Add event to session timeline"""
        self.events.append({
            "type": event_type,
            "time": datetime.now().isoformat(),
            "concept_id": concept_id,
            **kwargs
        })
        if concept_id and concept_id not in self.concepts_covered:
            self.concepts_covered.append(concept_id)
    
    def complete_session(self):
        """Mark session as completed"""
        self.end_time = datetime.now()
        self.status = "COMPLETED"
        if self.start_time:
            duration = (self.end_time - self.start_time).total_seconds() / 60
            self.final_state["total_duration_minutes"] = round(duration, 2)
        self.final_state["concepts_completed"] = len(self.concepts_covered)


class ConceptEpisode(Episode):
    """
    Track concept interaction history.
    
    Neo4j: (SessionEpisode)-[:COVERS_CONCEPT]->(ConceptEpisode)
    """
    episode_type: EpisodeType = EpisodeType.CONCEPT
    concept_id: str
    first_encountered: datetime = Field(default_factory=datetime.now)
    revisit_count: int = 0
    
    # Mastery progression over time
    mastery_progression: List[Dict[str, Any]] = Field(default_factory=list)
    # [{timestamp, bloom_level, score, difficulty}]
    
    # Current state
    current_bloom_level: str = "REMEMBER"
    current_mastery: float = 0.0
    
    def record_interaction(self, score: float, bloom_level: str, difficulty: int = 2):
        """Record an interaction with this concept"""
        self.mastery_progression.append({
            "timestamp": datetime.now().isoformat(),
            "bloom_level": bloom_level,
            "score": score,
            "difficulty": difficulty
        })
        self.current_bloom_level = bloom_level
        self.current_mastery = score
        self.revisit_count += 1


class ErrorEpisode(Episode):
    """
    Track misconception/error.
    
    Neo4j: (ConceptEpisode)-[:HAS_ERROR]->(ErrorEpisode)
    """
    episode_type: EpisodeType = EpisodeType.ERROR
    error_id: str
    concept_id: str
    
    # Error details
    misconception_type: str  # e.g., "Confusing WHERE with HAVING"
    severity: int = 3  # 1-5 (1=minor, 5=critical)
    
    # Remediation
    remediation_taken: Optional[str] = None
    remediated_at: Optional[datetime] = None
    remediation_successful: bool = False
    
    # Context
    question_id: Optional[str] = None
    learner_answer: Optional[str] = None
    expected_answer: Optional[str] = None
    
    def mark_remediated(self, method: str, successful: bool = True):
        """Mark error as remediated"""
        self.remediation_taken = method
        self.remediated_at = datetime.now()
        self.remediation_successful = successful


class ArtifactEpisode(Episode):
    """
    Track generated notes/artifacts.
    
    Neo4j: (ConceptEpisode)-[:HAS_ARTIFACT]->(ArtifactEpisode)
    """
    episode_type: EpisodeType = EpisodeType.ARTIFACT
    artifact_id: str
    concept_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Note details
    note_type: str = "atomic_note"  # atomic_note, concept_map, code_snippet
    note_reference: str = ""  # "learner_id.note.001"
    
    # Content summary
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Links
    linked_concepts: List[str] = Field(default_factory=list)
    linked_notes: List[str] = Field(default_factory=list)
