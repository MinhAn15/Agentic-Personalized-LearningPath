import json
import uuid
from typing import Dict, Any
from datetime import datetime
import logging

from backend.core.base_agent import BaseAgent, AgentType
from backend.models import (
    LearnerInput, LearnerProfile, LearnerProfileOutput,
    MasteryMap, SkillLevel, LearningStyle
)
from backend.prompts import LEARNER_PROFILER_SYSTEM_PROMPT
from llama_index.llms.openai import OpenAI
from backend.config import get_settings

logger = logging.getLogger(__name__)

class ProfilerAgent(BaseAgent):
    """
    Learner Profiler Agent - Understand learners and create personalized profiles.
    
    Responsibility:
    - Parse learner's natural language description
    - Extract: goal, timeline, current knowledge, learning style
    - Create learner profile
    - Initialize Personal KG for learner
    - Save to PostgreSQL + Redis cache
    
    Process Flow:
    1. Receive learner message
    2. Call LLM to parse and extract profile data
    3. Validate extracted data
    4. Create learner record in PostgreSQL
    5. Initialize Personal KG in Neo4j
    6. Cache profile in Redis
    7. Return profile + recommendations
    8. Emit event for planner agent
    
    Example:
        agent = ProfilerAgent(...)
        result = await agent.execute(
            learner_message="I want to learn SQL JOINs in 2 weeks..."
        )
        # Returns: {
        #   "success": True,
        #   "learner_id": "user_123",
        #   "profile": {...},
        #   "recommendations": [...]
        # }
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        """
        Initialize Profiler Agent.
        
        Args:
            agent_id: Unique agent identifier
            state_manager: Central state manager
            event_bus: Event bus for inter-agent communication
            llm: LLM instance (OpenAI by default)
        """
        super().__init__(agent_id, AgentType.PROFILER, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or OpenAI(
            model=self.settings.OPENAI_MODEL,
            api_key=self.settings.OPENAI_API_KEY
        )
        self.logger = logging.getLogger(f"ProfilerAgent.{agent_id}")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method.
        
        Args:
            learner_message: str - Learner's natural language description
            learner_name: str - Learner's name (optional)
            
        Returns:
            Dict with learner profile and recommendations
        """
        try:
            learner_message = kwargs.get("learner_message")
            learner_name = kwargs.get("learner_name", "Learner")
            
            if not learner_message:
                return {
                    "success": False,
                    "error": "learner_message is required",
                    "agent_id": self.agent_id
                }
            
            self.logger.info(f"👤 Profiling learner: {learner_name}")
            
            # Step 1: Extract profile data from learner message using LLM
            extraction_result = await self._extract_profile_from_llm(
                learner_message,
                learner_name
            )
            
            if not extraction_result["success"]:
                return extraction_result
            
            profile_data = extraction_result["profile_data"]
            learner_id = f"user_{uuid.uuid4().hex[:8]}"
            
            # Step 2: Create learner profile object
            profile = LearnerProfile(
                learner_id=learner_id,
                name=learner_name,
                goal=profile_data["goal"],
                time_available=profile_data["time_available"],
                preferred_learning_style=LearningStyle(profile_data["preferred_learning_style"]),
                current_skill_level=SkillLevel(profile_data["current_skill_level"]),
                current_mastery=[
                    MasteryMap(
                        concept_id=concept_id,
                        mastery_level=mastery
                    )
                    for concept_id, mastery in profile_data.get("current_mastery_map", {}).items()
                ],
                prerequisites_met=profile_data.get("prerequisites_met", [])
            )
            
            # Step 3: Save learner to PostgreSQL
            postgres = self.state_manager.postgres
            await postgres.create_learner(
                learner_id=learner_id,
                profile={
                    "name": profile.name,
                    "goal": profile.goal,
                    "time_available": profile.time_available,
                    "learning_style": profile.preferred_learning_style.value,
                    "skill_level": profile.current_skill_level.value,
                    "created_at": profile.created_at.isoformat()
                }
            )
            
            # Step 4: Initialize Personal KG for learner in Neo4j
            neo4j = self.state_manager.neo4j
            # Create learner node
            await neo4j.run_query(
                """
                CREATE (l:Learner {
                    learner_id: $learner_id,
                    name: $name,
                    goal: $goal
                })
                """,
                learner_id=learner_id,
                name=learner_name,
                goal=profile.goal
            )
            
            # Step 5: Cache profile in Redis
            redis = self.state_manager.redis
            await redis.set(
                f"profile:{learner_id}",
                {
                    "learner_id": learner_id,
                    "name": profile.name,
                    "goal": profile.goal,
                    "learning_style": profile.preferred_learning_style.value,
                    "skill_level": profile.current_skill_level.value
                },
                ttl=3600  # 1 hour cache
            )
            
            # Step 6: Build response
            result = {
                "success": True,
                "agent_id": self.agent_id,
                "learner_id": learner_id,
                "profile": {
                    "learner_id": profile.learner_id,
                    "name": profile.name,
                    "goal": profile.goal,
                    "time_available": profile.time_available,
                    "learning_style": profile.preferred_learning_style.value,
                    "skill_level": profile.current_skill_level.value,
                    "prerequisites_met": profile.prerequisites_met
                },
                "recommendations": profile_data.get("recommendations", []),
                "estimated_hours": profile_data.get("estimated_hours", 20)
            }
            
            # Step 7: Emit event for planner agent
            await self.send_message(
                receiver="planner",
                message_type="learner_profiled",
                payload={
                    "learner_id": learner_id,
                    "goal": profile.goal,
                    "time_available": profile.time_available
                }
            )
            
            self.logger.info(f"✅ Learner profile created: {learner_id}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ Profiling failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    async def _extract_profile_from_llm(
        self,
        learner_message: str,
        learner_name: str
    ) -> Dict[str, Any]:
        """
        Call LLM to extract learner profile from natural language.
        
        Args:
            learner_message: Natural language description from learner
            learner_name: Learner's name
            
        Returns:
            Dict with success flag and extracted profile data
        """
        try:
            user_prompt = f"""
            Learner Name: {learner_name}
            
            Learner's Message:
            "{learner_message}"
            
            Extract the learner's goal, timeline, current knowledge, learning style, and skill level.
            Return ONLY valid JSON, no markdown formatting.
            """
            
            # Call LLM
            response = await self.llm.acomplete(
                LEARNER_PROFILER_SYSTEM_PROMPT + "\n\n" + user_prompt
            )
            
            # Parse LLM response
            response_text = response.text
            
            try:
                # Extract JSON
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    profile_data = json.loads(json_str)
                else:
                    return {
                        "success": False,
                        "error": "Could not find JSON in LLM response"
                    }
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing error: {e}")
                return {
                    "success": False,
                    "error": f"Invalid JSON from LLM: {e}"
                }
            
            # Build mastery map from current knowledge
            current_mastery_map = {}
            for concept in profile_data.get("current_mastery", []):
                current_mastery_map[concept["concept_id"]] = concept["mastery_level"]
            
            profile_data["current_mastery_map"] = current_mastery_map
            
            return {
                "success": True,
                "profile_data": profile_data
            }
        
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return {
                "success": False,
                "error": f"LLM error: {e}"
            }
