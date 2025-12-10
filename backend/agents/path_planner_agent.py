from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.rl_engine import RLEngine, BanditStrategy
from backend.models import LearnerProfile
from backend.config import get_settings

logger = logging.getLogger(__name__)

class PathPlannerAgent(BaseAgent):
    """
    Path Planner Agent - Plan optimal learning sequences using RL.
    
    Responsibility:
    - Receive learner profile + course KG
    - Use multi-armed bandit to select optimal concept sequence
    - Respect prerequisites and learner constraints
    - Generate learning path with pacing recommendations
    - Adapt path as learner progresses
    
    Process Flow:
    1. Receive learner profile + course KG
    2. Initialize RL engine with concepts
    3. Calculate initial concept rewards
    4. Generate learning path day-by-day
    5. Recommend resources for each concept
    6. Return path + recommendations
    7. Listen for evaluation feedback to adapt path
    
    Example:
        agent = PathPlannerAgent(...)
        result = await agent.execute(
            learner_id="user_123",
            goal="Master SQL JOINs"
        )
        # Returns: {
        #   "success": True,
        #   "learning_path": [...],
        #   "pacing": "MODERATE",
        #   "success_probability": 0.92
        # }
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        """
        Initialize Path Planner Agent.
        
        Args:
            agent_id: Unique agent identifier
            state_manager: Central state manager
            event_bus: Event bus for inter-agent communication
            llm: LLM instance (optional, for resource recommendations)
        """
        super().__init__(agent_id, AgentType.PATH_PLANNER, state_manager, event_bus)
        
        self.settings = get_settings()
        self.rl_engine = RLEngine(strategy=BanditStrategy.UCB)
        self.logger = logging.getLogger(f"PathPlannerAgent.{agent_id}")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method.
        
        Args:
            learner_id: str - Learner ID
            goal: str - Learning goal (optional, can use from profile)
            
        Returns:
            Dict with learning path and recommendations
        """
        try:
            learner_id = kwargs.get("learner_id")
            goal = kwargs.get("goal")
            
            if not learner_id:
                return {
                    "success": False,
                    "error": "learner_id is required",
                    "agent_id": self.agent_id
                }
            
            self.logger.info(f"🧠 Planning learning path for: {learner_id}")
            
            # Step 1: Get learner profile
            learner_profile = await self.state_manager.get_learner_profile(learner_id)
            if not learner_profile:
                return {
                    "success": False,
                    "error": f"Learner profile not found: {learner_id}",
                    "agent_id": self.agent_id
                }
            
            # Step 2: Get Course KG from Neo4j
            neo4j = self.state_manager.neo4j
            course_concepts = await neo4j.run_query(
                "MATCH (c:CourseConcept) RETURN c.concept_id as concept_id, c.name as name, c.difficulty as difficulty"
            )
            course_relationships = await neo4j.run_query(
                "MATCH (a:CourseConcept)-[r:REQUIRES]->(b:CourseConcept) RETURN a.concept_id as source, b.concept_id as target"
            )
            
            if not course_concepts:
                return {
                    "success": False,
                    "error": "No concepts found in Course KG",
                    "agent_id": self.agent_id
                }
            
            # Step 3: Initialize RL engine with concepts
            for concept in course_concepts:
                self.rl_engine.add_arm(
                    concept['concept_id'],
                    concept.get('difficulty', 2)
                )
            
            # Step 4: Build prerequisite map
            prerequisites = {}
            for rel in course_relationships:
                concept = rel['source']
                required = rel['target']
                if concept not in prerequisites:
                    prerequisites[concept] = []
                prerequisites[concept].append(required)
            
            # Step 5: Generate learning path
            learning_path = await self._generate_learning_path(
                learner_profile=learner_profile,
                course_concepts=course_concepts,
                prerequisites=prerequisites
            )
            
            if not learning_path["success"]:
                return learning_path
            
            # Step 6: Recommend resources (from Neo4j or metadata)
            resources = await self._recommend_resources(
                learning_path["path"],
                learner_profile
            )
            
            # Step 7: Calculate success probability
            success_prob = await self._calculate_success_probability(
                learner_profile,
                learning_path["path"]
            )
            
            result = {
                "success": True,
                "agent_id": self.agent_id,
                "learner_id": learner_id,
                "learning_path": learning_path["path"],
                "pacing": learning_path["pacing"],
                "success_probability": success_prob,
                "total_estimated_hours": learning_path["total_hours"],
                "resources": resources
            }
            
            # Step 8: Save path to state
            await self.save_state(
                f"path:{learner_id}",
                result
            )
            
            # Step 9: Emit event for tutor agent
            await self.send_message(
                receiver="tutor",
                message_type="path_planned",
                payload={
                    "learner_id": learner_id,
                    "first_concept": learning_path["path"][0]["concept"] if learning_path["path"] else None,
                    "total_concepts": len(learning_path["path"])
                }
            )
            
            self.logger.info(f"✅ Learning path generated: {len(learning_path['path'])} concepts")
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ Path planning failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    async def _generate_learning_path(
        self,
        learner_profile: Dict[str, Any],
        course_concepts: List[Dict[str, Any]],
        prerequisites: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Generate day-by-day learning path using RL.
        
        Args:
            learner_profile: Learner's profile
            course_concepts: List of course concepts
            prerequisites: Prerequisite relationships
            
        Returns:
            Dict with path and metadata
        """
        try:
            path = []
            current_mastery = {
                m["concept_id"]: m["mastery_level"]
                for m in learner_profile.get("current_mastery", [])
            }
            
            time_available = learner_profile.get("time_available", 30)  # Days
            hours_per_day = learner_profile.get("hours_per_day", 2)
            total_hours = time_available * hours_per_day
            hours_used = 0
            day = 1
            
            while hours_used < total_hours * 0.8:  # Use 80% of available time
                # Select next concept using RL
                next_concept = self.rl_engine.select_concept(
                    learner_mastery=current_mastery,
                    prerequisites=prerequisites,
                    time_available=int(total_hours - hours_used),
                    learning_style=learner_profile.get("preferred_learning_style", "VISUAL")
                )
                
                if not next_concept:
                    break  # No more eligible concepts
                
                # Get concept details
                concept = next(
                    (c for c in course_concepts if c['concept_id'] == next_concept),
                    None
                )
                if not concept:
                    continue
                
                # Estimate hours needed based on difficulty
                difficulty = concept.get('difficulty', 2)
                estimated_hours = difficulty * 2  # 2-10 hours per concept
                
                # Check if fits in remaining time
                if hours_used + estimated_hours > total_hours:
                    break
                
                # Add to path
                path.append({
                    "day": day,
                    "concept": next_concept,
                    "concept_name": concept.get('name', next_concept),
                    "difficulty": difficulty,
                    "estimated_hours": estimated_hours,
                    "recommended_type": self._recommend_content_type(
                        difficulty,
                        learner_profile.get("preferred_learning_style", "VISUAL")
                    )
                })
                
                # Update tracking
                hours_used += estimated_hours
                current_mastery[next_concept] = 0.3  # Initial partial mastery
                day = int(hours_used / hours_per_day) + 1
            
            # Determine pacing
            if len(path) == 0:
                pacing = "NO_PATH"
            elif hours_used > total_hours * 0.9:
                pacing = "AGGRESSIVE"
            elif hours_used > total_hours * 0.7:
                pacing = "MODERATE"
            else:
                pacing = "RELAXED"
            
            return {
                "success": True,
                "path": path,
                "pacing": pacing,
                "total_hours": hours_used
            }
        
        except Exception as e:
            self.logger.error(f"Path generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _recommend_resources(
        self,
        learning_path: List[Dict[str, Any]],
        learner_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Recommend learning resources for each concept in path.
        
        Args:
            learning_path: Learning path
            learner_profile: Learner's profile
            
        Returns:
            List of resource recommendations
        """
        resources = []
        learning_style = learner_profile.get("preferred_learning_style", "VISUAL")
        
        for step in learning_path:
            concept = step["concept"]
            
            # In real implementation, query Neo4j for linked resources
            # For now, generate recommendations based on style
            
            resource = {
                "concept": concept,
                "recommended_resources": [
                    {
                        "type": "VIDEO",
                        "priority": 1 if learning_style == "VISUAL" else 2,
                        "description": f"Video tutorial on {step['concept_name']}"
                    },
                    {
                        "type": "EXERCISE",
                        "priority": 1,
                        "description": f"Practice exercises for {step['concept_name']}"
                    },
                    {
                        "type": "ARTICLE",
                        "priority": 2 if learning_style == "READING" else 3,
                        "description": f"Detailed article on {step['concept_name']}"
                    }
                ]
            }
            resources.append(resource)
        
        return resources
    
    async def _calculate_success_probability(
        self,
        learner_profile: Dict[str, Any],
        learning_path: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate probability of success for this learning path.
        
        Formula:
        - Start with learner's current average mastery
        - Add time available bonus
        - Subtract difficulty penalty
        - Clamp to 0-1 range
        
        Args:
            learner_profile: Learner's profile
            learning_path: Learning path
            
        Returns:
            Success probability (0-1)
        """
        if not learning_path:
            return 0.0
        
        # Current average mastery
        current_mastery = learner_profile.get("current_mastery", [])
        avg_mastery = sum(m.get("mastery_level", 0) for m in current_mastery) / max(len(current_mastery), 1)
        
        # Average difficulty of path
        avg_difficulty = sum(s.get("difficulty", 2) for s in learning_path) / len(learning_path)
        
        # Time factor
        time_available = learner_profile.get("time_available", 30)
        total_hours = sum(s.get("estimated_hours", 0) for s in learning_path)
        time_factor = min(total_hours / (time_available * 2), 1.0)
        
        # Calculate probability
        prob = avg_mastery + (0.3 * time_factor) - (0.1 * (avg_difficulty / 5.0))
        
        return max(0.0, min(1.0, prob))
    
    def _recommend_content_type(self, difficulty: int, learning_style: str) -> str:
        """Recommend content type based on difficulty and style"""
        if difficulty <= 2:
            return "TUTORIAL"
        elif difficulty <= 3:
            return "VIDEO"
        else:
            return "EXERCISE"
