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
    confidence: float = Field(ge=0, le=1)  # 0-1 confidence score

class DocumentInput(BaseModel):
    """Input document for knowledge extraction"""
    content: str
    document_type: DocumentType = DocumentType.LECTURE
    title: str = ""
    source_url: Optional[str] = None

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

class MasteryMap(BaseModel):
    """Learner's current mastery of concepts"""
    concept_id: str
    mastery_level: float = Field(ge=0, le=1)  # 0-1
    last_updated: datetime = Field(default_factory=datetime.now)

class LearnerProfile(BaseModel):
    """Complete learner profile"""
    learner_id: str
    name: str
    goal: str                           # What they want to learn
    time_available: int                 # Days until deadline
    preferred_learning_style: LearningStyle
    current_skill_level: SkillLevel
    current_mastery: List[MasteryMap]   # Mastery of each concept
    prerequisites_met: List[str]        # Concepts they already know
    created_at: datetime = Field(default_factory=datetime.now)
    
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
