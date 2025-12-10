"""
KAG (Knowledge Artifact Generation) Agent

Responsible for:
- Generating learning artifacts (summaries, flashcards, etc.)
- Creating personalized study materials
- Producing knowledge representations
- Building study guides and cheat sheets
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import logging

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.event_bus import EventType, Event

logger = logging.getLogger(__name__)


class ArtifactType(str, Enum):
    """Types of learning artifacts"""
    SUMMARY = "summary"
    FLASHCARD = "flashcard"
    MIND_MAP = "mind_map"
    CHEAT_SHEET = "cheat_sheet"
    STUDY_GUIDE = "study_guide"
    PRACTICE_PROBLEMS = "practice_problems"
    CONCEPT_MAP = "concept_map"
    QUIZ = "quiz"


@dataclass
class LearningArtifact:
    """A generated learning artifact"""
    artifact_id: str
    artifact_type: ArtifactType
    title: str
    content: Any  # Structure depends on type
    concept_ids: List[str]
    user_id: Optional[str]
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "title": self.title,
            "content": self.content,
            "concept_ids": self.concept_ids,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Flashcard:
    """A single flashcard"""
    card_id: str
    front: str
    back: str
    concept_id: str
    difficulty: float = 0.5
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "card_id": self.card_id,
            "front": self.front,
            "back": self.back,
            "concept_id": self.concept_id,
            "difficulty": self.difficulty,
            "tags": self.tags
        }


class KAGAgent(BaseAgent):
    """
    Knowledge Artifact Generation Agent.
    
    Generates various learning artifacts:
    - Summaries: Concise concept overviews
    - Flashcards: Spaced repetition cards
    - Mind Maps: Visual concept relationships
    - Cheat Sheets: Quick reference guides
    - Study Guides: Comprehensive learning materials
    - Practice Problems: Applied exercises
    
    Uses LLM for content generation and personalization.
    """
    
    def __init__(
        self,
        agent_id: str,
        state_manager: Any,
        event_bus: Any,
        llm: Optional[Any] = None
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.KAG,
            state_manager=state_manager,
            event_bus=event_bus
        )
        self.llm = llm
        self.artifacts: Dict[str, LearningArtifact] = {}
    
    async def execute(
        self,
        user_id: str,
        action: str = "generate",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute KAG actions.
        
        Args:
            user_id: The learner's ID
            action: Action to perform (generate, get_artifact, 
                   list_artifacts, regenerate)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing action results
        """
        self.logger.info(f"📚 KAG action: {action} for user {user_id}")
        
        try:
            if action == "generate":
                return await self._generate_artifact(user_id, **kwargs)
            
            elif action == "generate_flashcards":
                return await self._generate_flashcards(user_id, **kwargs)
            
            elif action == "generate_summary":
                return await self._generate_summary(user_id, **kwargs)
            
            elif action == "generate_mind_map":
                return await self._generate_mind_map(user_id, **kwargs)
            
            elif action == "generate_study_guide":
                return await self._generate_study_guide(user_id, **kwargs)
            
            elif action == "get_artifact":
                return await self._get_artifact(user_id, **kwargs)
            
            elif action == "list_artifacts":
                return await self._list_artifacts(user_id, **kwargs)
            
            else:
                return {"status": "error", "error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"❌ KAG action failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _generate_artifact(
        self,
        user_id: str,
        artifact_type: str,
        concept_ids: List[str],
        concepts_data: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a learning artifact of specified type"""
        
        artifact_type_enum = ArtifactType(artifact_type)
        
        if artifact_type_enum == ArtifactType.FLASHCARD:
            return await self._generate_flashcards(
                user_id, concept_ids=concept_ids, concepts_data=concepts_data
            )
        elif artifact_type_enum == ArtifactType.SUMMARY:
            return await self._generate_summary(
                user_id, concept_ids=concept_ids, concepts_data=concepts_data
            )
        elif artifact_type_enum == ArtifactType.MIND_MAP:
            return await self._generate_mind_map(
                user_id, concept_ids=concept_ids, concepts_data=concepts_data
            )
        elif artifact_type_enum == ArtifactType.STUDY_GUIDE:
            return await self._generate_study_guide(
                user_id, concept_ids=concept_ids, concepts_data=concepts_data
            )
        else:
            return {"status": "error", "error": f"Unsupported artifact type: {artifact_type}"}
    
    async def _generate_flashcards(
        self,
        user_id: str,
        concept_ids: List[str],
        concepts_data: Optional[List[Dict]] = None,
        cards_per_concept: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate flashcards for concepts"""
        
        import hashlib
        artifact_id = hashlib.md5(
            f"flashcards:{user_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        flashcards = []
        
        for i, concept_id in enumerate(concept_ids):
            concept_name = concept_id
            if concepts_data and i < len(concepts_data):
                concept_name = concepts_data[i].get("name", concept_id)
            
            # Generate cards for this concept
            for j in range(cards_per_concept):
                card = self._create_mock_flashcard(
                    card_id=f"{artifact_id}_c{i}_q{j}",
                    concept_id=concept_id,
                    concept_name=concept_name,
                    card_number=j
                )
                flashcards.append(card)
        
        artifact = LearningArtifact(
            artifact_id=artifact_id,
            artifact_type=ArtifactType.FLASHCARD,
            title=f"Flashcards: {len(concept_ids)} concepts",
            content=[card.to_dict() for card in flashcards],
            concept_ids=concept_ids,
            user_id=user_id,
            metadata={"card_count": len(flashcards)}
        )
        
        self.artifacts[artifact_id] = artifact
        await self.save_state(f"artifact:{artifact_id}", artifact.to_dict())
        
        self.logger.info(f"✅ Generated {len(flashcards)} flashcards")
        
        return {
            "status": "success",
            "artifact": artifact.to_dict()
        }
    
    def _create_mock_flashcard(
        self,
        card_id: str,
        concept_id: str,
        concept_name: str,
        card_number: int
    ) -> Flashcard:
        """Create a mock flashcard"""
        
        templates = [
            ("What is {concept}?", "A definition of {concept}..."),
            ("Why is {concept} important?", "Because {concept} enables..."),
            ("How does {concept} work?", "The mechanism of {concept} involves..."),
        ]
        
        template = templates[card_number % len(templates)]
        
        return Flashcard(
            card_id=card_id,
            front=template[0].format(concept=concept_name),
            back=template[1].format(concept=concept_name),
            concept_id=concept_id,
            difficulty=0.5 + (card_number * 0.1),
            tags=[concept_name.lower().replace(" ", "_")]
        )
    
    async def _generate_summary(
        self,
        user_id: str,
        concept_ids: List[str],
        concepts_data: Optional[List[Dict]] = None,
        style: str = "concise",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a summary for concepts"""
        
        import hashlib
        artifact_id = hashlib.md5(
            f"summary:{user_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Build summary content
        sections = []
        for i, concept_id in enumerate(concept_ids):
            concept_name = concept_id
            if concepts_data and i < len(concepts_data):
                concept_name = concepts_data[i].get("name", concept_id)
            
            sections.append({
                "concept_id": concept_id,
                "title": concept_name,
                "summary": self._mock_summary(concept_name, style),
                "key_points": [
                    f"Key point 1 about {concept_name}",
                    f"Key point 2 about {concept_name}",
                    f"Key point 3 about {concept_name}"
                ]
            })
        
        artifact = LearningArtifact(
            artifact_id=artifact_id,
            artifact_type=ArtifactType.SUMMARY,
            title=f"Summary: {len(concept_ids)} concepts",
            content={
                "style": style,
                "sections": sections
            },
            concept_ids=concept_ids,
            user_id=user_id
        )
        
        self.artifacts[artifact_id] = artifact
        await self.save_state(f"artifact:{artifact_id}", artifact.to_dict())
        
        self.logger.info(f"✅ Generated summary for {len(concept_ids)} concepts")
        
        return {
            "status": "success",
            "artifact": artifact.to_dict()
        }
    
    def _mock_summary(self, concept: str, style: str) -> str:
        """Generate mock summary text"""
        
        if style == "concise":
            return f"{concept} is a fundamental concept that involves..."
        elif style == "detailed":
            return f"""
{concept} Overview:

{concept} represents an important area of study. Understanding {concept} 
requires familiarity with several core principles.

Key aspects include:
1. The theoretical foundation
2. Practical applications
3. Common challenges and solutions

Mastering {concept} opens doors to advanced topics.
"""
        else:
            return f"Introduction to {concept}..."
    
    async def _generate_mind_map(
        self,
        user_id: str,
        concept_ids: List[str],
        concepts_data: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a mind map structure"""
        
        import hashlib
        artifact_id = hashlib.md5(
            f"mindmap:{user_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Build mind map structure
        nodes = []
        edges = []
        
        # Central node
        central_node = {
            "id": "central",
            "label": "Learning Path",
            "type": "central"
        }
        nodes.append(central_node)
        
        # Concept nodes
        for i, concept_id in enumerate(concept_ids):
            concept_name = concept_id
            if concepts_data and i < len(concepts_data):
                concept_name = concepts_data[i].get("name", concept_id)
            
            node = {
                "id": f"concept_{i}",
                "label": concept_name,
                "type": "concept",
                "concept_id": concept_id
            }
            nodes.append(node)
            
            edges.append({
                "source": "central",
                "target": f"concept_{i}",
                "type": "contains"
            })
            
            # Add sub-nodes
            for j in range(2):
                sub_node = {
                    "id": f"concept_{i}_sub_{j}",
                    "label": f"Subtopic {j+1}",
                    "type": "subtopic"
                }
                nodes.append(sub_node)
                edges.append({
                    "source": f"concept_{i}",
                    "target": f"concept_{i}_sub_{j}",
                    "type": "includes"
                })
        
        artifact = LearningArtifact(
            artifact_id=artifact_id,
            artifact_type=ArtifactType.MIND_MAP,
            title=f"Mind Map: {len(concept_ids)} concepts",
            content={
                "nodes": nodes,
                "edges": edges,
                "layout": "radial"
            },
            concept_ids=concept_ids,
            user_id=user_id
        )
        
        self.artifacts[artifact_id] = artifact
        await self.save_state(f"artifact:{artifact_id}", artifact.to_dict())
        
        self.logger.info(f"✅ Generated mind map with {len(nodes)} nodes")
        
        return {
            "status": "success",
            "artifact": artifact.to_dict()
        }
    
    async def _generate_study_guide(
        self,
        user_id: str,
        concept_ids: List[str],
        concepts_data: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a comprehensive study guide"""
        
        import hashlib
        artifact_id = hashlib.md5(
            f"studyguide:{user_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        chapters = []
        
        for i, concept_id in enumerate(concept_ids):
            concept_name = concept_id
            if concepts_data and i < len(concepts_data):
                concept_name = concepts_data[i].get("name", concept_id)
            
            chapter = {
                "chapter_number": i + 1,
                "title": concept_name,
                "concept_id": concept_id,
                "sections": [
                    {
                        "title": "Overview",
                        "content": f"Introduction to {concept_name}..."
                    },
                    {
                        "title": "Key Concepts",
                        "content": f"The main ideas behind {concept_name}..."
                    },
                    {
                        "title": "Examples",
                        "content": f"Practical examples of {concept_name}..."
                    },
                    {
                        "title": "Practice Questions",
                        "content": f"Test your understanding of {concept_name}..."
                    }
                ],
                "key_takeaways": [
                    f"Takeaway 1 for {concept_name}",
                    f"Takeaway 2 for {concept_name}"
                ]
            }
            chapters.append(chapter)
        
        artifact = LearningArtifact(
            artifact_id=artifact_id,
            artifact_type=ArtifactType.STUDY_GUIDE,
            title=f"Study Guide: {len(concept_ids)} chapters",
            content={
                "chapters": chapters,
                "total_estimated_time": len(concept_ids) * 30,  # minutes
                "recommended_schedule": "1 chapter per day"
            },
            concept_ids=concept_ids,
            user_id=user_id
        )
        
        self.artifacts[artifact_id] = artifact
        await self.save_state(f"artifact:{artifact_id}", artifact.to_dict())
        
        self.logger.info(f"✅ Generated study guide with {len(chapters)} chapters")
        
        return {
            "status": "success",
            "artifact": artifact.to_dict()
        }
    
    async def _get_artifact(
        self,
        user_id: str,
        artifact_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Get a specific artifact"""
        
        if artifact_id in self.artifacts:
            return {
                "status": "success",
                "artifact": self.artifacts[artifact_id].to_dict()
            }
        
        saved = await self.load_state(f"artifact:{artifact_id}")
        if saved:
            return {
                "status": "success",
                "artifact": saved
            }
        
        return {"status": "not_found", "error": "Artifact not found"}
    
    async def _list_artifacts(
        self,
        user_id: str,
        artifact_type: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """List artifacts for user"""
        
        user_artifacts = [
            a.to_dict() for a in self.artifacts.values()
            if a.user_id == user_id
        ]
        
        if artifact_type:
            user_artifacts = [
                a for a in user_artifacts
                if a["artifact_type"] == artifact_type
            ]
        
        return {
            "status": "success",
            "artifacts": user_artifacts,
            "count": len(user_artifacts)
        }
