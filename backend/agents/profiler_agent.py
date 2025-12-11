import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

from backend.core.base_agent import BaseAgent, AgentType
from backend.models import (
    LearnerInput, LearnerProfile, LearnerProfileOutput,
    MasteryMap, SkillLevel, LearningStyle
)
from backend.prompts import LEARNER_PROFILER_SYSTEM_PROMPT
from llama_index.llms.gemini import Gemini
from backend.config import get_settings

logger = logging.getLogger(__name__)


class DiagnosticState(str, Enum):
    """Diagnostic Assessment States"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ProfilerAgent(BaseAgent):
    """
    Learner Profiler Agent - Build and update Learner Profile.
    
    Features (per Thesis):
    1. Goal Parsing & Intent Extraction (Topic, Purpose, Constraint, Level)
    2. Diagnostic Assessment System (3-5 representative concepts)
    3. Profile Vectorization [KnowledgeState, LearningStyle, GoalEmbedding]
    
    Process Flow:
    1. Receive learner message
    2. Parse goal (Topic, Purpose, Timeline, Level)
    3. If new profile -> Trigger diagnostic assessment
    4. Assess answers and estimate initial mastery
    5. Create profile in PostgreSQL + Personal KG in Neo4j
    6. Cache in Redis
    7. Emit event for planner
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        super().__init__(agent_id, AgentType.PROFILER, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or Gemini(
            model=self.settings.GEMINI_MODEL,
            api_key=self.settings.GOOGLE_API_KEY
        )
        self.logger = logging.getLogger(f"ProfilerAgent.{agent_id}")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Main execution method."""
        try:
            learner_message = kwargs.get("learner_message")
            learner_name = kwargs.get("learner_name", "Learner")
            skip_diagnostic = kwargs.get("skip_diagnostic", False)
            
            if not learner_message:
                return {
                    "success": False,
                    "error": "learner_message is required",
                    "agent_id": self.agent_id
                }
            
            self.logger.info(f"👤 Profiling learner: {learner_name}")
            
            # Step 1: Parse goal with Intent Extraction
            goal_result = await self._parse_goal_with_intent(
                learner_message, learner_name
            )
            
            if not goal_result["success"]:
                return goal_result
            
            profile_data = goal_result["profile_data"]
            learner_id = f"user_{uuid.uuid4().hex[:8]}"
            
            # Step 2: Diagnostic Assessment (if not skipped)
            diagnostic_result = None
            initial_mastery = {}
            
            if not skip_diagnostic:
                diagnostic_result = await self._run_diagnostic_assessment(
                    learner_id=learner_id,
                    topic=profile_data["topic"],
                    current_level=profile_data.get("current_level", "unknown")
                )
                
                if diagnostic_result["success"]:
                    initial_mastery = diagnostic_result["mastery_estimates"]
            
            # Step 3: Create learner profile object
            profile = LearnerProfile(
                learner_id=learner_id,
                name=learner_name,
                goal=profile_data["goal"],
                time_available=profile_data.get("time_available", 30),
                preferred_learning_style=LearningStyle(
                    profile_data.get("preferred_learning_style", "VISUAL")
                ),
                current_skill_level=SkillLevel(
                    profile_data.get("current_skill_level", "BEGINNER")
                ),
                current_mastery=[
                    MasteryMap(concept_id=cid, mastery_level=level)
                    for cid, level in initial_mastery.items()
                ],
                prerequisites_met=profile_data.get("prerequisites_met", [])
            )
            
            # Step 4: Profile Vectorization
            profile_vector = await self._vectorize_profile(profile, profile_data)
            
            # Step 5: Save to PostgreSQL
            postgres = self.state_manager.postgres
            await postgres.create_learner(
                learner_id=learner_id,
                profile={
                    "name": profile.name,
                    "goal": profile.goal,
                    "topic": profile_data["topic"],
                    "purpose": profile_data.get("purpose", ""),
                    "time_available": profile.time_available,
                    "learning_style": profile.preferred_learning_style.value,
                    "skill_level": profile.current_skill_level.value,
                    "profile_vector": profile_vector.tolist() if hasattr(profile_vector, 'tolist') else profile_vector,
                    "created_at": profile.created_at.isoformat()
                }
            )
            
            # Step 6: Initialize Personal KG in Neo4j
            neo4j = self.state_manager.neo4j
            await neo4j.run_query(
                """
                CREATE (l:Learner {
                    learner_id: $learner_id,
                    name: $name,
                    goal: $goal,
                    topic: $topic,
                    purpose: $purpose,
                    skill_level: $skill_level,
                    learning_style: $learning_style,
                    created_at: datetime()
                })
                """,
                learner_id=learner_id,
                name=learner_name,
                goal=profile.goal,
                topic=profile_data["topic"],
                purpose=profile_data.get("purpose", ""),
                skill_level=profile.current_skill_level.value,
                learning_style=profile.preferred_learning_style.value
            )
            
            # Create initial mastery relationships
            for concept_id, mastery in initial_mastery.items():
                await neo4j.run_query(
                    """
                    MATCH (l:Learner {learner_id: $learner_id})
                    MATCH (c:CourseConcept {concept_id: $concept_id})
                    MERGE (l)-[m:HAS_MASTERY]->(c)
                    SET m.level = $mastery, m.updated_at = datetime()
                    """,
                    learner_id=learner_id,
                    concept_id=concept_id,
                    mastery=mastery
                )
            
            # Step 7: Cache in Redis
            redis = self.state_manager.redis
            await redis.set(
                f"profile:{learner_id}",
                {
                    "learner_id": learner_id,
                    "name": profile.name,
                    "goal": profile.goal,
                    "topic": profile_data["topic"],
                    "learning_style": profile.preferred_learning_style.value,
                    "skill_level": profile.current_skill_level.value,
                    "diagnostic_completed": diagnostic_result is not None
                },
                ttl=3600
            )
            
            # Build response
            result = {
                "success": True,
                "agent_id": self.agent_id,
                "learner_id": learner_id,
                "profile": {
                    "learner_id": profile.learner_id,
                    "name": profile.name,
                    "goal": profile.goal,
                    "topic": profile_data["topic"],
                    "purpose": profile_data.get("purpose", ""),
                    "time_available": profile.time_available,
                    "learning_style": profile.preferred_learning_style.value,
                    "skill_level": profile.current_skill_level.value,
                    "prerequisites_met": profile.prerequisites_met
                },
                "diagnostic": {
                    "completed": diagnostic_result is not None,
                    "questions_asked": diagnostic_result["questions_count"] if diagnostic_result else 0,
                    "initial_mastery": initial_mastery
                },
                "recommendations": profile_data.get("recommendations", []),
                "estimated_hours": profile_data.get("estimated_hours", 20)
            }
            
            # Emit event for planner
            await self.send_message(
                receiver="planner",
                message_type="learner_profiled",
                payload={
                    "learner_id": learner_id,
                    "goal": profile.goal,
                    "topic": profile_data["topic"],
                    "time_available": profile.time_available,
                    "initial_mastery": initial_mastery
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
    
    async def _parse_goal_with_intent(
        self, learner_message: str, learner_name: str
    ) -> Dict[str, Any]:
        """
        Parse learner goal with Intent Extraction.
        
        Extracts:
        - Topic: Main subject to learn
        - Purpose: Why (job, project, curiosity)
        - Constraint: Time limit
        - Current Level: Skill assessment
        """
        try:
            prompt = f"""
You are analyzing a learner's goal. Extract structured information.

Learner Name: {learner_name}
Learner's Message: "{learner_message}"

Extract:
1. topic: Main subject/skill to learn (e.g., "SQL", "Python", "Machine Learning")
2. purpose: Why they want to learn (e.g., "Data Analysis", "Job Interview", "Project")
3. goal: Full goal statement
4. time_available: Days available (default 30)
5. current_skill_level: BEGINNER, INTERMEDIATE, or ADVANCED
6. preferred_learning_style: VISUAL, AUDITORY, READING, or KINESTHETIC
7. recommendations: 2-3 learning recommendations based on goal
8. estimated_hours: Total hours needed

Return ONLY valid JSON:
{{
  "topic": "SQL",
  "purpose": "Data Analysis",
  "goal": "Master SQL for data analysis in 2 weeks",
  "time_available": 14,
  "current_skill_level": "BEGINNER",
  "preferred_learning_style": "VISUAL",
  "recommendations": ["Start with SELECT statements", "Practice with real datasets"],
  "estimated_hours": 20,
  "current_mastery": []
}}
"""
            response = await self.llm.acomplete(prompt)
            response_text = response.text
            
            try:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    profile_data = json.loads(response_text[json_start:json_end])
                    return {"success": True, "profile_data": profile_data}
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing error: {e}")
            
            return {"success": False, "error": "Could not parse goal"}
        
        except Exception as e:
            self.logger.error(f"Goal parsing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _run_diagnostic_assessment(
        self, learner_id: str, topic: str, current_level: str
    ) -> Dict[str, Any]:
        """
        Diagnostic Assessment Strategy.
        
        1. Select 3-5 representative concepts from Course KG (high centrality)
        2. Generate diagnostic questions
        3. Assess answers (simulated in this version)
        4. Estimate initial mastery for concept clusters
        """
        try:
            # Get high-centrality concepts from Course KG
            neo4j = self.state_manager.neo4j
            concepts = await neo4j.run_query(
                """
                MATCH (c:CourseConcept)
                WHERE toLower(c.name) CONTAINS toLower($topic)
                   OR any(tag IN c.semantic_tags WHERE toLower(tag) CONTAINS toLower($topic))
                WITH c, size((c)-[:REQUIRES]->()) + size((c)<-[:REQUIRES]-()) as centrality
                ORDER BY centrality DESC
                LIMIT 5
                RETURN c.concept_id as concept_id, c.name as name, c.difficulty as difficulty
                """,
                topic=topic
            )
            
            if not concepts:
                # Fallback: generate questions based on topic
                concepts = await self._generate_diagnostic_concepts(topic)
            
            # Generate diagnostic questions
            questions = await self._generate_diagnostic_questions(concepts, topic)
            
            # In a real system, we would:
            # 1. Present questions to learner
            # 2. Collect answers
            # 3. Evaluate answers
            # For now, estimate based on stated level
            
            mastery_estimates = {}
            level_multiplier = {
                "beginner": 0.1,
                "intermediate": 0.5,
                "advanced": 0.8,
                "unknown": 0.2
            }.get(current_level.lower(), 0.2)
            
            for concept in concepts:
                concept_id = concept.get("concept_id") or concept.get("name", "").upper().replace(" ", "_")
                difficulty = concept.get("difficulty", 2)
                
                # Estimate mastery (inverse relationship with difficulty for beginners)
                base_mastery = level_multiplier * (1 - (difficulty - 1) * 0.1)
                mastery_estimates[concept_id] = max(0.0, min(1.0, base_mastery))
            
            return {
                "success": True,
                "questions_count": len(questions),
                "concepts_assessed": [c.get("concept_id") or c.get("name") for c in concepts],
                "mastery_estimates": mastery_estimates,
                "diagnostic_questions": questions
            }
        
        except Exception as e:
            self.logger.error(f"Diagnostic assessment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_diagnostic_concepts(self, topic: str) -> List[Dict]:
        """Generate representative concepts for a topic if not in KG"""
        prompt = f"""
Generate 5 key concepts for learning {topic}, from basic to advanced.

Return ONLY valid JSON array:
[
  {{"concept_id": "TOPIC_CONCEPT1", "name": "Basic Concept", "difficulty": 1}},
  {{"concept_id": "TOPIC_CONCEPT2", "name": "Intermediate Concept", "difficulty": 2}},
  ...
]
"""
        response = await self.llm.acomplete(prompt)
        response_text = response.text
        
        try:
            json_start = response_text.find("[")
            json_end = response_text.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
        except:
            pass
        
        return []
    
    async def _generate_diagnostic_questions(
        self, concepts: List[Dict], topic: str
    ) -> List[Dict]:
        """Generate diagnostic questions for concepts"""
        questions = []
        
        for concept in concepts:
            concept_name = concept.get("name", concept.get("concept_id", topic))
            difficulty = concept.get("difficulty", 2)
            
            prompt = f"""
Generate ONE diagnostic question to assess understanding of "{concept_name}" (difficulty: {difficulty}/5).

Return ONLY valid JSON:
{{
  "question": "Your question here?",
  "expected_answer_keywords": ["keyword1", "keyword2"],
  "difficulty": {difficulty},
  "concept_id": "{concept.get('concept_id', concept_name.upper().replace(' ', '_'))}"
}}
"""
            response = await self.llm.acomplete(prompt)
            response_text = response.text
            
            try:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    question = json.loads(response_text[json_start:json_end])
                    questions.append(question)
            except:
                pass
        
        return questions
    
    async def _vectorize_profile(
        self, profile: LearnerProfile, profile_data: Dict
    ) -> List[float]:
        """
        Profile Vectorization.
        
        Creates vector: [KnowledgeState, LearningStyle, GoalEmbedding]
        """
        # Knowledge State (simplified - would use embeddings in production)
        mastery_values = [m.mastery_level for m in profile.current_mastery] or [0.0]
        knowledge_state = sum(mastery_values) / len(mastery_values)
        
        # Learning Style (one-hot encoding)
        style_map = {
            "VISUAL": [1, 0, 0, 0],
            "AUDITORY": [0, 1, 0, 0],
            "READING": [0, 0, 1, 0],
            "KINESTHETIC": [0, 0, 0, 1]
        }
        learning_style = style_map.get(profile.preferred_learning_style.value, [0.25, 0.25, 0.25, 0.25])
        
        # Skill Level
        level_map = {
            "BEGINNER": 0.2,
            "INTERMEDIATE": 0.5,
            "ADVANCED": 0.8
        }
        skill_level = level_map.get(profile.current_skill_level.value, 0.2)
        
        # Goal embedding (simplified - would use sentence embeddings in production)
        goal_features = [
            profile.time_available / 90,  # Normalized time (max 90 days)
            skill_level,
            len(profile_data.get("topic", "")) / 50  # Topic length feature
        ]
        
        # Combine into profile vector
        profile_vector = [knowledge_state] + learning_style + [skill_level] + goal_features
        
        return profile_vector
