"""
Learner Profiler Agent

Responsible for:
- Building and maintaining learner profiles
- Tracking knowledge state and skill levels
- Analyzing learning preferences and styles
- Detecting knowledge gaps
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import logging

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.event_bus import EventType, Event

logger = logging.getLogger(__name__)


class LearningStyle(str, Enum):
    """Learning style preferences (VARK model)"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING_WRITING = "reading_writing"
    KINESTHETIC = "kinesthetic"


class SkillLevel(str, Enum):
    """Bloom's Taxonomy levels"""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class KnowledgeState:
    """Represents learner's knowledge state for a concept"""
    
    def __init__(
        self,
        concept_id: str,
        concept_name: str,
        skill_level: SkillLevel,
        confidence: float,  # 0.0 to 1.0
        last_assessed: Optional[datetime] = None,
        practice_count: int = 0
    ):
        self.concept_id = concept_id
        self.concept_name = concept_name
        self.skill_level = skill_level
        self.confidence = confidence
        self.last_assessed = last_assessed or datetime.now()
        self.practice_count = practice_count
    
    def to_dict(self) -> Dict:
        return {
            "concept_id": self.concept_id,
            "concept_name": self.concept_name,
            "skill_level": self.skill_level.value,
            "confidence": self.confidence,
            "last_assessed": self.last_assessed.isoformat(),
            "practice_count": self.practice_count
        }


class LearnerProfile:
    """Complete learner profile"""
    
    def __init__(
        self,
        user_id: str,
        name: str,
        learning_styles: Optional[List[LearningStyle]] = None,
        knowledge_states: Optional[Dict[str, KnowledgeState]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        goals: Optional[List[str]] = None
    ):
        self.user_id = user_id
        self.name = name
        self.learning_styles = learning_styles or []
        self.knowledge_states = knowledge_states or {}
        self.preferences = preferences or {
            "session_duration": 30,  # minutes
            "difficulty_preference": "adaptive",
            "practice_frequency": "daily",
            "feedback_style": "detailed"
        }
        self.goals = goals or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "learning_styles": [style.value for style in self.learning_styles],
            "knowledge_states": {
                k: v.to_dict() for k, v in self.knowledge_states.items()
            },
            "preferences": self.preferences,
            "goals": self.goals,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ProfilerAgent(BaseAgent):
    """
    Agent responsible for learner profiling and assessment.
    
    Uses:
    - Initial assessment quizzes
    - Learning history analysis
    - Performance tracking
    - Knowledge Tracing algorithms (BKT, DKT)
    
    Outputs:
    - Learner profiles
    - Knowledge states per concept
    - Learning style preferences
    - Knowledge gaps analysis
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
            agent_type=AgentType.PROFILER,
            state_manager=state_manager,
            event_bus=event_bus
        )
        self.llm = llm
        self.profiles: Dict[str, LearnerProfile] = {}
        
        # Subscribe to relevant events
        self.event_bus.subscribe(
            EventType.USER_ASSESSMENT,
            self._on_assessment_event
        )
        self.event_bus.subscribe(
            EventType.USER_PROGRESS,
            self._on_progress_event
        )
    
    async def execute(
        self,
        user_id: str,
        action: str = "get_profile",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute profiler actions.
        
        Args:
            user_id: The learner's ID
            action: Action to perform (get_profile, update_knowledge, 
                   analyze_gaps, assess_style)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing action results
        """
        self.logger.info(f"👤 Profiler action: {action} for user {user_id}")
        
        try:
            if action == "get_profile":
                return await self._get_or_create_profile(user_id, **kwargs)
            
            elif action == "update_knowledge":
                return await self._update_knowledge_state(user_id, **kwargs)
            
            elif action == "analyze_gaps":
                return await self._analyze_knowledge_gaps(user_id, **kwargs)
            
            elif action == "assess_style":
                return await self._assess_learning_style(user_id, **kwargs)
            
            elif action == "update_preferences":
                return await self._update_preferences(user_id, **kwargs)
            
            else:
                return {"status": "error", "error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"❌ Profiler action failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _get_or_create_profile(
        self, 
        user_id: str,
        name: str = "Learner",
        **kwargs
    ) -> Dict[str, Any]:
        """Get existing profile or create new one"""
        
        # Check cache first
        if user_id in self.profiles:
            profile = self.profiles[user_id]
            self.logger.debug(f"📋 Retrieved cached profile for {user_id}")
        else:
            # Check state manager
            saved_profile = await self.load_state(f"profile:{user_id}")
            
            if saved_profile:
                profile = self._dict_to_profile(saved_profile)
                self.profiles[user_id] = profile
                self.logger.debug(f"📋 Loaded profile from state for {user_id}")
            else:
                # Create new profile
                profile = LearnerProfile(
                    user_id=user_id,
                    name=name
                )
                self.profiles[user_id] = profile
                await self.save_state(f"profile:{user_id}", profile.to_dict())
                self.logger.info(f"✨ Created new profile for {user_id}")
        
        return {
            "status": "success",
            "profile": profile.to_dict()
        }
    
    async def _update_knowledge_state(
        self,
        user_id: str,
        concept_id: str,
        concept_name: str,
        skill_level: str,
        confidence: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Update knowledge state for a concept"""
        
        profile_result = await self._get_or_create_profile(user_id)
        profile = self.profiles[user_id]
        
        # Update or create knowledge state
        knowledge_state = KnowledgeState(
            concept_id=concept_id,
            concept_name=concept_name,
            skill_level=SkillLevel(skill_level),
            confidence=confidence,
            practice_count=kwargs.get("practice_count", 0)
        )
        
        profile.knowledge_states[concept_id] = knowledge_state
        profile.updated_at = datetime.now()
        
        # Save to state
        await self.save_state(f"profile:{user_id}", profile.to_dict())
        
        # Publish progress event
        await self.event_bus.publish(Event(
            event_type=EventType.USER_PROGRESS,
            source=self.agent_id,
            payload={
                "user_id": user_id,
                "concept_id": concept_id,
                "skill_level": skill_level,
                "confidence": confidence
            }
        ))
        
        self.logger.info(
            f"📊 Updated knowledge state: {concept_name} -> {skill_level}"
        )
        
        return {
            "status": "success",
            "knowledge_state": knowledge_state.to_dict()
        }
    
    async def _analyze_knowledge_gaps(
        self,
        user_id: str,
        target_concepts: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze knowledge gaps"""
        
        profile_result = await self._get_or_create_profile(user_id)
        profile = self.profiles[user_id]
        
        gaps = []
        weak_areas = []
        
        for concept_id, state in profile.knowledge_states.items():
            # Low confidence indicates a gap
            if state.confidence < 0.5:
                gaps.append({
                    "concept_id": concept_id,
                    "concept_name": state.concept_name,
                    "current_level": state.skill_level.value,
                    "confidence": state.confidence,
                    "recommendation": "needs_review"
                })
            # Medium confidence indicates weak area
            elif state.confidence < 0.7:
                weak_areas.append({
                    "concept_id": concept_id,
                    "concept_name": state.concept_name,
                    "current_level": state.skill_level.value,
                    "confidence": state.confidence,
                    "recommendation": "needs_practice"
                })
        
        # Sort by confidence (lowest first)
        gaps.sort(key=lambda x: x["confidence"])
        weak_areas.sort(key=lambda x: x["confidence"])
        
        self.logger.info(
            f"🔍 Found {len(gaps)} gaps, {len(weak_areas)} weak areas"
        )
        
        return {
            "status": "success",
            "gaps": gaps,
            "weak_areas": weak_areas,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def _assess_learning_style(
        self,
        user_id: str,
        responses: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Assess learning style based on questionnaire/behavior"""
        
        profile_result = await self._get_or_create_profile(user_id)
        profile = self.profiles[user_id]
        
        # Mock assessment - would use actual questionnaire responses
        # VARK scoring would go here
        styles = [LearningStyle.VISUAL, LearningStyle.READING_WRITING]
        
        profile.learning_styles = styles
        profile.updated_at = datetime.now()
        
        await self.save_state(f"profile:{user_id}", profile.to_dict())
        
        self.logger.info(
            f"🎯 Assessed learning styles: {[s.value for s in styles]}"
        )
        
        return {
            "status": "success",
            "learning_styles": [style.value for style in styles],
            "primary_style": styles[0].value if styles else None
        }
    
    async def _update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Update learner preferences"""
        
        profile_result = await self._get_or_create_profile(user_id)
        profile = self.profiles[user_id]
        
        profile.preferences.update(preferences)
        profile.updated_at = datetime.now()
        
        await self.save_state(f"profile:{user_id}", profile.to_dict())
        
        return {
            "status": "success",
            "preferences": profile.preferences
        }
    
    def _dict_to_profile(self, data: Dict) -> LearnerProfile:
        """Convert dict back to LearnerProfile"""
        profile = LearnerProfile(
            user_id=data["user_id"],
            name=data["name"],
            learning_styles=[
                LearningStyle(s) for s in data.get("learning_styles", [])
            ],
            preferences=data.get("preferences", {}),
            goals=data.get("goals", [])
        )
        
        # Reconstruct knowledge states
        for concept_id, state_data in data.get("knowledge_states", {}).items():
            profile.knowledge_states[concept_id] = KnowledgeState(
                concept_id=state_data["concept_id"],
                concept_name=state_data["concept_name"],
                skill_level=SkillLevel(state_data["skill_level"]),
                confidence=state_data["confidence"],
                practice_count=state_data.get("practice_count", 0)
            )
        
        return profile
    
    async def _on_assessment_event(self, event: Event) -> None:
        """Handle assessment events"""
        self.logger.debug(f"📥 Assessment event from {event.source}")
    
    async def _on_progress_event(self, event: Event) -> None:
        """Handle progress events"""
        if event.source != self.agent_id:
            self.logger.debug(f"📥 Progress event from {event.source}")
