"""
Tutor Agent (Harvard Principles)

Responsible for:
- Delivering personalized learning content
- Applying Harvard learning principles
- Adaptive teaching strategies
- Socratic questioning method
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import logging

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.event_bus import EventType, Event

logger = logging.getLogger(__name__)


class TeachingStrategy(str, Enum):
    """Teaching strategies based on Harvard principles"""
    DIRECT_INSTRUCTION = "direct_instruction"
    SOCRATIC = "socratic"
    SCAFFOLDED = "scaffolded"
    DISCOVERY = "discovery"
    WORKED_EXAMPLES = "worked_examples"
    INTERLEAVED = "interleaved"


class ContentType(str, Enum):
    """Types of learning content"""
    EXPLANATION = "explanation"
    EXAMPLE = "example"
    PRACTICE = "practice"
    QUIZ = "quiz"
    SUMMARY = "summary"
    MISCONCEPTION = "misconception"


@dataclass
class LearningContent:
    """A piece of learning content"""
    content_id: str
    concept_id: str
    content_type: ContentType
    title: str
    body: str
    difficulty: float
    estimated_time: int  # minutes
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        return {
            "content_id": self.content_id,
            "concept_id": self.concept_id,
            "content_type": self.content_type.value,
            "title": self.title,
            "body": self.body,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "metadata": self.metadata or {}
        }


@dataclass
class TutoringSession:
    """A tutoring session state"""
    session_id: str
    user_id: str
    concept_id: str
    strategy: TeachingStrategy
    contents_delivered: List[str]
    interactions: List[Dict]
    started_at: datetime
    current_state: str = "active"
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "concept_id": self.concept_id,
            "strategy": self.strategy.value,
            "contents_delivered": self.contents_delivered,
            "interactions": self.interactions,
            "started_at": self.started_at.isoformat(),
            "current_state": self.current_state
        }


class TutorAgent(BaseAgent):
    """
    Agent responsible for delivering personalized tutoring.
    
    Harvard Learning Principles Applied:
    1. Active learning over passive consumption
    2. Spaced repetition for retention
    3. Interleaved practice
    4. Immediate feedback
    5. Metacognitive awareness
    
    Teaching Strategies:
    - Socratic questioning
    - Scaffolded learning
    - Worked examples with fading
    - Discovery-based learning
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
            agent_type=AgentType.TUTOR,
            state_manager=state_manager,
            event_bus=event_bus
        )
        self.llm = llm
        self.sessions: Dict[str, TutoringSession] = {}
        self.content_cache: Dict[str, LearningContent] = {}
    
    async def execute(
        self,
        user_id: str,
        action: str = "start_session",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute tutor actions.
        
        Args:
            user_id: The learner's ID
            action: Action to perform (start_session, get_content,
                   ask_question, provide_feedback, end_session)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing action results
        """
        self.logger.info(f"📚 Tutor action: {action} for user {user_id}")
        
        try:
            if action == "start_session":
                return await self._start_session(user_id, **kwargs)
            
            elif action == "get_content":
                return await self._get_content(user_id, **kwargs)
            
            elif action == "ask_question":
                return await self._handle_question(user_id, **kwargs)
            
            elif action == "provide_hint":
                return await self._provide_hint(user_id, **kwargs)
            
            elif action == "explain_concept":
                return await self._explain_concept(user_id, **kwargs)
            
            elif action == "socratic_dialogue":
                return await self._socratic_dialogue(user_id, **kwargs)
            
            elif action == "end_session":
                return await self._end_session(user_id, **kwargs)
            
            else:
                return {"status": "error", "error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"❌ Tutor action failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _start_session(
        self,
        user_id: str,
        concept_id: str,
        concept_name: str,
        learner_profile: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Start a new tutoring session"""
        
        import hashlib
        session_id = hashlib.md5(
            f"{user_id}:{concept_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Select teaching strategy based on learner profile
        strategy = self._select_strategy(learner_profile)
        
        session = TutoringSession(
            session_id=session_id,
            user_id=user_id,
            concept_id=concept_id,
            strategy=strategy,
            contents_delivered=[],
            interactions=[],
            started_at=datetime.now()
        )
        
        self.sessions[session_id] = session
        await self.save_state(f"session:{session_id}", session.to_dict())
        
        # Generate initial content
        initial_content = await self._generate_initial_content(
            concept_id, concept_name, strategy
        )
        
        self.logger.info(
            f"✅ Started session {session_id} with {strategy.value} strategy"
        )
        
        return {
            "status": "success",
            "session_id": session_id,
            "strategy": strategy.value,
            "initial_content": initial_content
        }
    
    def _select_strategy(
        self, 
        learner_profile: Optional[Dict]
    ) -> TeachingStrategy:
        """Select teaching strategy based on learner profile"""
        
        if not learner_profile:
            return TeachingStrategy.SCAFFOLDED
        
        # Get learner preferences
        styles = learner_profile.get("learning_styles", [])
        knowledge_level = learner_profile.get("knowledge_level", "beginner")
        
        # Strategy selection logic
        if knowledge_level == "beginner":
            return TeachingStrategy.WORKED_EXAMPLES
        elif knowledge_level == "intermediate":
            return TeachingStrategy.SCAFFOLDED
        elif knowledge_level == "advanced":
            return TeachingStrategy.SOCRATIC
        
        return TeachingStrategy.SCAFFOLDED
    
    async def _generate_initial_content(
        self,
        concept_id: str,
        concept_name: str,
        strategy: TeachingStrategy
    ) -> Dict[str, Any]:
        """Generate initial content based on strategy"""
        
        if strategy == TeachingStrategy.WORKED_EXAMPLES:
            return {
                "type": "worked_example",
                "title": f"Introduction to {concept_name}",
                "content": self._mock_worked_example(concept_name),
                "next_steps": ["Try a similar example", "Ask a question"]
            }
        
        elif strategy == TeachingStrategy.SOCRATIC:
            return {
                "type": "socratic_question",
                "title": f"Let's explore {concept_name}",
                "content": self._mock_socratic_question(concept_name),
                "next_steps": ["Answer the question", "Get a hint"]
            }
        
        elif strategy == TeachingStrategy.SCAFFOLDED:
            return {
                "type": "scaffolded_intro",
                "title": f"Learning {concept_name} step by step",
                "content": self._mock_scaffolded_content(concept_name),
                "next_steps": ["Continue to next step", "Review prerequisites"]
            }
        
        return {
            "type": "explanation",
            "title": concept_name,
            "content": f"Let's learn about {concept_name}..."
        }
    
    def _mock_worked_example(self, concept: str) -> str:
        """Mock worked example content"""
        return f"""
## Worked Example: {concept}

### Problem
Let's solve a practical problem involving {concept}.

### Step 1: Understand
First, let's identify what we need to know...

### Step 2: Plan
Now, let's plan our approach...

### Step 3: Execute
Following our plan...

### Step 4: Verify
Let's check our work...

### Key Takeaways
- Point 1 about {concept}
- Point 2 about {concept}
- Point 3 about {concept}
"""
    
    def _mock_socratic_question(self, concept: str) -> str:
        """Mock Socratic questioning content"""
        return f"""
🤔 **Let's think together about {concept}**

Before I explain {concept} to you, I'd like you to consider:

**Question:** What do you think {concept} means, and why might it be important?

Take a moment to think about this. Even if you're not sure, making a guess helps your brain prepare to learn!

*When you're ready, share your thoughts and I'll help guide your understanding.*
"""
    
    def _mock_scaffolded_content(self, concept: str) -> str:
        """Mock scaffolded content"""
        return f"""
## {concept}: A Step-by-Step Guide

We'll learn {concept} in 4 progressive steps:

### 🟢 Step 1: Foundation (You are here)
Understanding the basics...

### 🔵 Step 2: Core Concepts
Building on the foundation...

### 🟡 Step 3: Application
Putting it into practice...

### 🔴 Step 4: Mastery
Advanced understanding...

---

*Let's start with Step 1...*
"""
    
    async def _get_content(
        self,
        user_id: str,
        session_id: str,
        content_type: str = "next",
        **kwargs
    ) -> Dict[str, Any]:
        """Get learning content for session"""
        
        if session_id not in self.sessions:
            return {"status": "error", "error": "Session not found"}
        
        session = self.sessions[session_id]
        
        # Generate appropriate content
        content = {
            "content_id": f"{session_id}_{len(session.contents_delivered)}",
            "type": content_type,
            "body": f"Content for {session.concept_id}...",
            "timestamp": datetime.now().isoformat()
        }
        
        session.contents_delivered.append(content["content_id"])
        
        return {
            "status": "success",
            "content": content
        }
    
    async def _handle_question(
        self,
        user_id: str,
        session_id: str,
        question: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle learner question"""
        
        if session_id not in self.sessions:
            return {"status": "error", "error": "Session not found"}
        
        session = self.sessions[session_id]
        
        # Record interaction
        session.interactions.append({
            "type": "question",
            "content": question,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate response (would use LLM)
        response = f"Great question! Let me explain more about that..."
        
        session.interactions.append({
            "type": "response",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "response": response
        }
    
    async def _provide_hint(
        self,
        user_id: str,
        session_id: str,
        context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Provide a hint without giving away the answer"""
        
        if session_id not in self.sessions:
            return {"status": "error", "error": "Session not found"}
        
        # Progressive hints (Harvard principle: scaffolded support)
        hints = [
            "Think about the relationship between the concepts...",
            "Consider what you already know about similar problems...",
            "Let me break this down: first, consider..."
        ]
        
        session = self.sessions[session_id]
        hint_index = min(
            len([i for i in session.interactions if i["type"] == "hint"]),
            len(hints) - 1
        )
        
        session.interactions.append({
            "type": "hint",
            "content": hints[hint_index],
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "hint": hints[hint_index],
            "hints_remaining": len(hints) - hint_index - 1
        }
    
    async def _explain_concept(
        self,
        user_id: str,
        concept_id: str,
        concept_name: str,
        depth: str = "standard",
        **kwargs
    ) -> Dict[str, Any]:
        """Explain a concept at specified depth"""
        
        if depth == "simple":
            explanation = f"{concept_name} in simple terms: ..."
        elif depth == "detailed":
            explanation = f"Detailed explanation of {concept_name}: ..."
        else:
            explanation = f"Understanding {concept_name}: ..."
        
        return {
            "status": "success",
            "concept_id": concept_id,
            "explanation": explanation,
            "depth": depth
        }
    
    async def _socratic_dialogue(
        self,
        user_id: str,
        session_id: str,
        learner_response: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Continue Socratic dialogue based on learner response"""
        
        if session_id not in self.sessions:
            return {"status": "error", "error": "Session not found"}
        
        session = self.sessions[session_id]
        
        # Record learner response
        session.interactions.append({
            "type": "learner_response",
            "content": learner_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate follow-up question (would use LLM)
        follow_up = """
Interesting perspective! Let me ask you this:

🤔 How does that relate to what happens when...?

*This follow-up question helps deepen understanding through guided discovery.*
"""
        
        session.interactions.append({
            "type": "socratic_follow_up",
            "content": follow_up,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "follow_up": follow_up,
            "interaction_count": len(session.interactions)
        }
    
    async def _end_session(
        self,
        user_id: str,
        session_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """End tutoring session"""
        
        if session_id not in self.sessions:
            return {"status": "error", "error": "Session not found"}
        
        session = self.sessions[session_id]
        session.current_state = "completed"
        
        # Generate session summary
        summary = {
            "session_id": session_id,
            "concept_id": session.concept_id,
            "duration_minutes": (
                datetime.now() - session.started_at
            ).total_seconds() / 60,
            "contents_viewed": len(session.contents_delivered),
            "interactions": len(session.interactions),
            "completed_at": datetime.now().isoformat()
        }
        
        await self.save_state(f"session:{session_id}", session.to_dict())
        
        self.logger.info(f"✅ Ended session {session_id}")
        
        return {
            "status": "success",
            "summary": summary
        }
