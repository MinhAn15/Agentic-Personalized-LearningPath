from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .enums import (
    SkillLevel, LearningStyle, DifficultyLevel,
    ConceptRelationType, DocumentType
)

# ============= KNOWLEDGE EXTRACTION SCHEMAS =============

class ConceptNode(BaseModel):
    """Single concept node for Course KG"""
    concept_id: str
    name: str
    description: str
    difficulty: DifficultyLevel
    document_source: str  # Which document it came from
    tags: List[str] = Field(default_factory=list)

class ConceptRelationship(BaseModel):
    """Relationship between two concepts"""
    source_concept_id: str
    target_concept_id: str
    relation_type: ConceptRelationType
    confidence: float = Field(ge=0, le=1)
    keywords: List[str] = Field(default_factory=list)
    summary: str = ""

class DocumentInput(BaseModel):
    """Input document for knowledge extraction"""
    content: str
    document_type: DocumentType = DocumentType.LECTURE
    title: str = ""
    source_url: Optional[str] = None
    force_real: bool = False

class KnowledgeExtractionOutput(BaseModel):
    """Output from knowledge extraction"""
    concepts: List[ConceptNode]
    relationships: List[ConceptRelationship]
    document_id: str
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    total_concepts: int
    total_relationships: int

# ============= LEARNER PROFILE SCHEMAS =============

class LearnerInput(BaseModel):
    """Input from learner describing their learning goal"""
    message: str  # Natural language input: "I want to learn SQL JOINs in 2 weeks..."
    learner_name: Optional[str] = None
    age: Optional[int] = None

class TutorInput(BaseModel):
    """Input for Tutor Agent"""
    learner_id: str
    question: str
    concept_id: str
    hint_level: Optional[int] = 1  # 0-5
    conversation_history: Optional[List[Dict[str, Any]]] = None
    force_real: bool = False

class EvaluationInput(BaseModel):
    """Input for Evaluator Agent"""
    learner_id: str
    concept_id: str
    learner_response: str
    expected_answer: str
    correct_answer_explanation: Optional[str] = None
    force_real: bool = False

class KAGInput(BaseModel):
    """Input for KAG Agent"""
    agent_id: str = "kag_agent"
    action: str = "analyze"  # analyze, generate_artifact
    payload: Dict[str, Any]
    force_real: bool = False

class MasteryMap(BaseModel):
    """Learner's current mastery of concepts"""
    concept_id: str
    mastery_level: float = Field(ge=0, le=1)  # 0-1
    bloom_level: str = "REMEMBER"  # Bloom's taxonomy level
    last_updated: datetime = Field(default_factory=datetime.now)

class LearnerProfile(BaseModel):
    """
    Complete learner profile with 17 dimensions (per THESIS Bảng 3.8).
    
    Categories:
    - Static (1-4): Demographics, learning goal, style
    - Dynamic (5-8): Updated each session
    - Episodic (9-14): History tracking
    - Computed (15-16): Derived metrics
    - Aggregated (17): Analytics
    """
    # ==========================================
    # STATIC DIMENSIONS (1-4)
    # ==========================================
    learner_id: str                                          # dim 1: UUID from registration
    demographic: Dict[str, Any] = Field(default_factory=dict)  # dim 2: {age, language, timezone, etc}
    learning_goal: List[str] = Field(default_factory=list)   # dim 3: ["SQL_SELECT", "SQL_JOIN", ...]
    learning_style: LearningStyle = LearningStyle.VISUAL     # dim 4: VISUAL/AUDITORY/READING/KINESTHETIC
    
    # ==========================================
    # DYNAMIC DIMENSIONS (5-8) - Updated each session
    # ==========================================
    skill_level: SkillLevel = SkillLevel.BEGINNER            # dim 5: BEGINNER/INTERMEDIATE/ADVANCED
    available_time: int = 30                                  # dim 6: minutes/week (updated weekly)
    preferences: Dict[str, Any] = Field(default_factory=lambda: {
        "pace": "medium",           # slow/medium/fast
        "verbosity": "normal",      # brief/normal/verbose
        "hint_level": 2,            # 1-3 (fewer to more hints)
        "difficulty_next": "MEDIUM" # EASY/MEDIUM/HARD
    })                                                        # dim 7
    constraints: Dict[str, Any] = Field(default_factory=lambda: {
        "blackout_hours": [],       # hours when unavailable
        "priority_skills": []       # skills to prioritize
    })                                                        # dim 8
    
    interest_tags: Dict[str, float] = Field(default_factory=dict) # NEW: Interest tracking for decay
    
    # ==========================================
    # EPISODIC DIMENSIONS (9-14) - History tracking
    # ==========================================
    concept_mastery_map: Dict[str, float] = Field(default_factory=dict)  # dim 9: {concept_id: 0-1}
    completed_concepts: List[str] = Field(default_factory=list)           # dim 10: concepts with PROCEED
    error_patterns: List[Dict[str, Any]] = Field(default_factory=list)    # dim 11: [{concept_id, misconception_type, severity}]
    session_history: List[Dict[str, Any]] = Field(default_factory=list)   # dim 12: [{session_id, start, end, concepts_covered}]
    interaction_log: List[Dict[str, Any]] = Field(default_factory=list)   # dim 13: [{role, content, timestamp}]
    artifact_ids: List[str] = Field(default_factory=list)                 # dim 14: [note_id1, note_id2, ...]
    
    # ==========================================
    # COMPUTED DIMENSIONS (15-16) - Derived metrics
    # ==========================================
    avg_mastery_level: float = 0.0                            # dim 15: mean(mastery_map.values())
    learning_velocity: float = 0.0                            # dim 16: concepts/hour
    
    # ==========================================
    # AGGREGATED DIMENSION (17)
    # ==========================================
    engagement_score: float = 0.0                             # dim 17: 0-1 from analytics
    
    # ==========================================
    # BLOOM'S TRACKING (per concept)
    # ==========================================
    mastery_progression: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    # {concept_id: {timestamp, bloom_level, score, difficulty}}
    
    # ==========================================
    # METADATA
    # ==========================================
    version: int = 0                                          # For optimistic locking
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    last_updated_by: str = "system"                           # "profiler", "planner", "tutor", etc.
    
    # Legacy fields (for backward compatibility)
    name: str = ""
    goal: str = ""
    time_available: int = 30  # Alias for available_time
    preferred_learning_style: LearningStyle = LearningStyle.VISUAL
    current_skill_level: SkillLevel = SkillLevel.BEGINNER
    current_mastery: List[MasteryMap] = Field(default_factory=list)
    prerequisites_met: List[str] = Field(default_factory=list)
    
    def recalculate_avg_mastery(self):
        """Recalculate dim 15: avg_mastery_level"""
        if self.concept_mastery_map:
            self.avg_mastery_level = sum(self.concept_mastery_map.values()) / len(self.concept_mastery_map)
        else:
            self.avg_mastery_level = 0.0
    
    def get_bloom_level(self, concept_id: str) -> str:
        """Get Bloom's level for a concept"""
        if concept_id in self.mastery_progression:
            return self.mastery_progression[concept_id].get("bloom_level", "REMEMBER")
        return "REMEMBER"

class LearnerProfileOutput(BaseModel):
    """Output from profiler agent"""
    profile: LearnerProfile
    recommendations: List[str]  # Initial recommendations
    estimated_hours: int       # Estimated hours needed
    profiling_timestamp: datetime = Field(default_factory=datetime.now)

# ============= AGENT COMMUNICATION SCHEMAS =============

class AgentExecutionRequest(BaseModel):
    """Request to execute an agent"""
    agent_type: str  # "knowledge_extraction", "profiler", etc.
    learner_id: Optional[str] = None
    payload: Dict[str, Any]

class AgentExecutionResponse(BaseModel):
    """Response from agent execution"""
    success: bool
    agent_type: str
    execution_time_ms: float
    result: Dict[str, Any]
    error: Optional[str] = None
