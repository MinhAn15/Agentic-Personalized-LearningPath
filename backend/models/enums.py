from enum import Enum

class SkillLevel(str, Enum):
    """Learner skill levels"""
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"

class LearningStyle(str, Enum):
    """Learning style preferences"""
    VISUAL = "VISUAL"           # Prefers diagrams, videos
    AUDITORY = "AUDITORY"       # Prefers spoken explanation
    READING = "READING"         # Prefers text, articles
    KINESTHETIC = "KINESTHETIC" # Prefers hands-on practice
    MIXED = "MIXED"             # No clear preference

class DifficultyLevel(int, Enum):
    """Concept difficulty levels (1-5)"""
    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5

class ConceptRelationType(str, Enum):
    """Types of relationships between concepts"""
    REQUIRES = "REQUIRES"           # A requires B (prerequisite)
    SIMILAR_TO = "SIMILAR_TO"       # Similar concepts
    IS_SUBCONCEPT_OF = "IS_SUBCONCEPT_OF"  # Hierarchical
    BUILDS_ON = "BUILDS_ON"         # Extends knowledge
    CONFLICTS_WITH = "CONFLICTS_WITH"  # Contradicts

class DocumentType(str, Enum):
    """Types of learning documents"""
    LECTURE = "LECTURE"
    TUTORIAL = "TUTORIAL"
    TEXTBOOK = "TEXTBOOK"
    EXERCISE = "EXERCISE"
    REFERENCE = "REFERENCE"

class EvaluationType(str, Enum):
    """Types of evaluations"""
    QUIZ = "QUIZ"
    EXERCISE = "EXERCISE"
    PROJECT = "PROJECT"
    EXAM = "EXAM"

class PathDecision(str, Enum):
    """Evaluator decisions for path planning"""
    PROCEED = "PROCEED"           # Continue to next concept
    REMEDIATE = "REMEDIATE"       # Go back to easier concept
    ALTERNATE = "ALTERNATE"       # Try alternative path
    MASTERED = "MASTERED"         # Concept fully understood
