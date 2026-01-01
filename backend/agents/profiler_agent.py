import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

from backend.core.base_agent import BaseAgent, AgentType
from backend.models import (
    LearnerInput, LearnerProfile, LearnerProfileOutput,
    MasteryMap, SkillLevel, LearningStyle,
    SessionEpisode, ConceptEpisode, ErrorEpisode, ArtifactEpisode, EpisodeType
)
from backend.prompts import LEARNER_PROFILER_SYSTEM_PROMPT
from llama_index.llms.gemini import Gemini
from llama_index.core import PropertyGraphIndex, StorageContext, load_index_from_storage
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.embeddings.gemini import GeminiEmbedding
from backend.config import get_settings
import os

logger = logging.getLogger(__name__)


class VersionConflictError(Exception):
    """Raised when optimistic locking fails"""
    pass


class DiagnosticState(str, Enum):
    """Diagnostic Assessment States"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ProfilerAgent(BaseAgent):
    """
    Learner Profiler Agent - Build and update 17-dimensional Learner Profile.
    
    Features (per THESIS Section 3.5.1):
    1. Goal Parsing & Intent Extraction (Topic, Purpose, Constraint, Level)
    2. Diagnostic Assessment System (3-5 representative concepts)
    3. Profile Vectorization (10 dimensions including Bloom's)
    4. Episodic Memory (4 episode types)
    5. Real-time Updates (event-driven)
    6. Personal KG Initialization (Dual-KG Layer 3)
    
    Event Subscriptions:
    - EVALUATION_COMPLETED: Update mastery + Bloom level
    - PACE_CHECK_TRIGGERED: Update learning velocity
    - ARTIFACT_CREATED: Track generated notes
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        super().__init__(agent_id, AgentType.PROFILER, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or Gemini(
            model=self.settings.GEMINI_MODEL,
            api_key=self.settings.GOOGLE_API_KEY
        )
        self.logger = logging.getLogger(f"ProfilerAgent.{agent_id}")
        
        # Per-learner locks for event ordering
        self._learner_locks: Dict[str, asyncio.Lock] = {}
        
        # Lazy loaded Retrievers
        self._graph_retriever = None
        self._vector_index = None
        
        # Subscribe to events for real-time updates
        self._subscribe_to_events()
    
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
            
            # Create initial MasteryNode for each concept (Change #4: Dual-KG Layer 3)
            for concept_id, mastery in initial_mastery.items():
                mastery_id = f"MASTERY_{learner_id}_{concept_id}"
                await neo4j.run_query(
                    """
                    MATCH (l:Learner {learner_id: $learner_id})
                    MATCH (c:CourseConcept {concept_id: $concept_id})
                    CREATE (m:MasteryNode {
                        mastery_id: $mastery_id,
                        learner_id: $learner_id,
                        concept_id: $concept_id,
                        level: $mastery_level,
                        bloom_level: 'REMEMBER',
                        created_at: datetime(),
                        last_updated: datetime()
                    })
                    CREATE (l)-[:HAS_MASTERY]->(m)
                    CREATE (m)-[:MAPS_TO_CONCEPT]->(c)
                    """,
                    learner_id=learner_id,
                    concept_id=concept_id,
                    mastery_id=mastery_id,
                    mastery_level=mastery
                )
            
            # Create initial SessionEpisode
            session_id = f"session_{learner_id}_{datetime.now().timestamp()}"
            await neo4j.run_query(
                """
                MATCH (l:Learner {learner_id: $learner_id})
                CREATE (s:SessionEpisode {
                    session_id: $session_id,
                    started_at: datetime(),
                    status: 'ACTIVE',
                    concepts_covered: $concepts_covered
                })
                CREATE (l)-[:HAS_SESSION]->(s)
                """,
                learner_id=learner_id,
                session_id=session_id,
                concepts_covered=list(initial_mastery.keys())
            )
            
            self.logger.info(f"Personal KG initialized: {len(initial_mastery)} MasteryNodes + SessionEpisode")
            
            # Step 7: Cache in Redis (including profile_vector for Agent 3 LinUCB)
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
                    "diagnostic_completed": diagnostic_result is not None,
                    "profile_vector": profile_vector,  # NEW: 10-dim vector for LinUCB
                    "time_available": profile.time_available,
                    "hours_per_day": profile_data.get("hours_per_day", 2)
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
    
    def _get_graph_retriever(self):
        """
        Lazy load LlamaIndex PropertyGraphIndex (Graph RAG).
        Connects to existing Neo4j graph.
        """
        if self._graph_retriever is None:
            try:
                # Initialize Graph Store connected to existing Neo4j
                graph_store = Neo4jPropertyGraphStore(
                    username=self.settings.NEO4J_USER,
                    password=self.settings.NEO4J_PASSWORD,
                    url=self.settings.NEO4J_URI,
                )
                
                # Create Index wrapper (no build, just load)
                # Ensure we use Gemini embeddings
                embed_model = GeminiEmbedding(
                    model_name="models/embedding-001",
                    api_key=self.settings.GOOGLE_API_KEY
                )
                
                index = PropertyGraphIndex.from_existing(
                    property_graph_store=graph_store,
                    embed_model=embed_model
                )
                
                # Hybrid Retriever: Vector + Keyword + Graph Traversal
                self._graph_retriever = index.as_retriever(
                    retriever_mode="hybrid", 
                    similarity_top_k=10 # Get broader set, then filter by centrality
                )
                self.logger.info("Loaded PropertyGraphIndex Retriever (Neo4j)")
                
            except Exception as e:
                self.logger.error(f"Failed to load Graph Retriever: {e}")
        return self._graph_retriever

    def _get_vector_index(self):
        """Lazy load vector index (Fallback)"""
        if self._vector_index is None:
            try:
                storage_dir = "./storage/vector_index"
                if os.path.exists(storage_dir):
                    storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
                    self._vector_index = load_index_from_storage(storage_context)
            except Exception as e:
                self.logger.warning(f"Failed to load fallback vector index: {e}")
        return self._vector_index

    async def _run_diagnostic_assessment(
        self, learner_id: str, topic: str, current_level: str
    ) -> Dict[str, Any]:
        """
        Diagnostic Assessment V2 (Robust Hybrid).
        
        Priority 1: PropertyGraphIndex (Graph RAG) - Best for Semantics+Topology
        Priority 2: VectorStoreIndex (Local) + Cypher (Graph) - Fallback
        Priority 3: Raw Cypher - Fallback
        Priority 4: LLM Generation - Last resort
        """
        try:
            concepts = []
            
            # 1. Try Graph RAG (PropertyGraphIndex)
            retriever = self._get_graph_retriever()
            if retriever:
                try:
                    nodes = await retriever.aretrieve(topic)
                    candidate_ids = [n.metadata.get("concept_id") or n.metadata.get("name") for n in nodes]
                    
                    if candidate_ids:
                        # Centrality Reranking
                        neo4j = self.state_manager.neo4j
                        concepts = await neo4j.run_query(
                            """
                            MATCH (c:CourseConcept)
                            WHERE c.concept_id IN $ids OR c.name IN $ids
                            WITH c, size((c)-[:REQUIRES]->()) + size((c)<-[:REQUIRES]-()) as centrality
                            ORDER BY centrality DESC
                            LIMIT 5
                            RETURN c.concept_id as concept_id, c.name as name, c.difficulty as difficulty
                            """,
                            ids=candidate_ids
                        )
                except Exception as e:
                     self.logger.warning(f"Graph RAG failed, trying fallback: {e}")
            
            # 2. Fallback: VectorStoreIndex + Cypher (If Graph RAG empty)
            if not concepts:
                index = self._get_vector_index()
                if index:
                    try:
                        retriever = index.as_retriever(similarity_top_k=5)
                        nodes = await retriever.aretrieve(topic)
                        candidate_ids = [n.metadata.get("concept_id") or n.metadata.get("name") for n in nodes]
                        
                        if candidate_ids:
                             neo4j = self.state_manager.neo4j
                             concepts = await neo4j.run_query(
                                """
                                MATCH (c:CourseConcept)
                                WHERE c.concept_id IN $ids OR c.name IN $ids
                                WITH c, size((c)-[:REQUIRES]->()) + size((c)<-[:REQUIRES]-()) as centrality
                                ORDER BY centrality DESC
                                LIMIT 5
                                RETURN c.concept_id as concept_id, c.name as name, c.difficulty as difficulty
                                """,
                                ids=candidate_ids
                            )
                    except Exception as e:
                        self.logger.warning(f"Vector fallback failed: {e}")
            
            # 3. Fallback: Raw Cypher (Keyword Search)
            if not concepts:
                # Fallback logic...
                neo4j = self.state_manager.neo4j
                concepts = await neo4j.run_query(
                    """
                    MATCH (c:CourseConcept)
                    WHERE toLower(c.name) CONTAINS toLower($topic)
                    WITH c, size((c)-[:REQUIRES]->()) + size((c)<-[:REQUIRES]-()) as centrality
                    ORDER BY centrality DESC
                    LIMIT 5
                    RETURN c.concept_id as concept_id, c.name as name, c.difficulty as difficulty
                    """,
                    topic=topic
                )
            
            if not concepts:
                # 4. Ultimate Fallback: LLM Generation
                concepts = await self._generate_diagnostic_concepts(topic)
            
            # ... Rest of logic ...
            
            # Generate diagnostic questions
            questions = await self._generate_diagnostic_questions(concepts, topic)
            
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
                
                # Estimate mastery
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
        
        # Time normalized
        time_normalized = profile.time_available / 500  # Normalize to 500 mins max
        
        # Change #5: Bloom's average level
        bloom_map = {
            "REMEMBER": 0.1, "UNDERSTAND": 0.3, "APPLY": 0.5,
            "ANALYZE": 0.7, "EVALUATE": 0.85, "CREATE": 1.0
        }
        bloom_values = []
        if hasattr(profile, 'mastery_progression') and profile.mastery_progression:
            for v in profile.mastery_progression.values():
                bloom_level = v.get('bloom_level', 'REMEMBER') if isinstance(v, dict) else 'REMEMBER'
                bloom_values.append(bloom_map.get(bloom_level, 0.1))
        bloom_avg = sum(bloom_values) / len(bloom_values) if bloom_values else 0.0
        
        # Learning velocity
        learning_velocity = profile.learning_velocity if hasattr(profile, 'learning_velocity') else 0.0
        
        # Topic features
        topic_length = len(profile_data.get("topic", "")) / 50
        
        # Combine into 10-dimension profile vector
        # [knowledge_state, visual, auditory, reading, kinesthetic, 
        #  skill_level, time_norm, bloom_avg, learning_vel, topic_len]
        profile_vector = [
            knowledge_state,       # dim 0: knowledge state
            *learning_style,       # dim 1-4: learning style one-hot
            skill_level,           # dim 5: skill level
            time_normalized,       # dim 6: time
            bloom_avg,             # dim 7: Bloom's average (NEW)
            learning_velocity,     # dim 8: learning velocity (NEW)
            topic_length           # dim 9: topic
        ]
        
        return profile_vector  # 10 dimensions
    
    # ==========================================
    # CHANGE #3: REAL-TIME UPDATE HANDLERS
    # ==========================================
    
    def _subscribe_to_events(self):
        """Subscribe to events for real-time profile updates"""
        if hasattr(self.event_bus, 'subscribe'):
            self.event_bus.subscribe("EVALUATION_COMPLETED", self._on_evaluation_completed)
            self.event_bus.subscribe("PACE_CHECK_TRIGGERED", self._on_pace_check)
            self.event_bus.subscribe("ARTIFACT_CREATED", self._on_artifact_created)
            # FIX Issue 6: Subscribe to KG_SYNC_COMPLETED from KAG Agent
            self.event_bus.subscribe("KG_SYNC_COMPLETED", self._on_kg_sync_completed)
            # FIX Issue 3 (Phase 5): Subscribe to ARTIFACT_GENERATION_FAILED from KAG Agent
            self.event_bus.subscribe("ARTIFACT_GENERATION_FAILED", self._on_artifact_generation_failed)
            self.logger.info("Subscribed to EVALUATION_COMPLETED, PACE_CHECK_TRIGGERED, ARTIFACT_CREATED, KG_SYNC_COMPLETED, ARTIFACT_GENERATION_FAILED")
    
    def _get_learner_lock(self, learner_id: str) -> asyncio.Lock:
        """Get per-learner lock for event ordering"""
        if learner_id not in self._learner_locks:
            self._learner_locks[learner_id] = asyncio.Lock()
        return self._learner_locks[learner_id]
    
    async def _on_evaluation_completed(self, event: Dict[str, Any]):
        """
        Update profile when Evaluator finishes.
        
        Updates:
        - concept_mastery_map (dim 9)
        - completed_concepts (dim 10) if score >= 0.8
        - error_patterns (dim 11) if misconceptions
        - mastery_progression (Bloom's)
        - avg_mastery_level (dim 15)
        """
        learner_id = event.get('learner_id')
        if not learner_id:
            return
        
        async with self._get_learner_lock(learner_id):
            try:
                concept_id = event['concept_id']
                score = event['score']  # 0-1
                misconceptions = event.get('misconceptions', [])
                question_difficulty = event.get('question_difficulty', 2)
                question_type = event.get('question_type', 'factual')
                
                # Get current profile from Redis/PostgreSQL
                redis = self.state_manager.redis
                profile_data = await redis.get(f"profile:{learner_id}")
                
                if not profile_data:
                    self.logger.warning(f"Profile not found for {learner_id}")
                    return
                
                version_before = profile_data.get('version', 0)
                prev_avg_mastery = profile_data.get('avg_mastery_level', 0)
                
                # 1. Update concept_mastery_map (dim 9)
                if 'concept_mastery_map' not in profile_data:
                    profile_data['concept_mastery_map'] = {}
                profile_data['concept_mastery_map'][concept_id] = score
                
                # 2. If PROCEED (score >= 0.8), add to completed_concepts (dim 10)
                if score >= 0.8:
                    if 'completed_concepts' not in profile_data:
                        profile_data['completed_concepts'] = []
                    if concept_id not in profile_data['completed_concepts']:
                        profile_data['completed_concepts'].append(concept_id)
                
                # 3. Apply Interest Decay (Mechanism 3)
                self._apply_interest_decay(profile_data)
                
                # 3. Add error episodes if misconceptions detected (dim 11)
                if misconceptions:
                    if 'error_patterns' not in profile_data:
                        profile_data['error_patterns'] = []
                    
                    for misc in misconceptions:
                        error_episode = {
                            'error_id': f"err_{uuid.uuid4().hex[:8]}",
                            'timestamp': datetime.now().isoformat(),
                            'concept_id': concept_id,
                            'misconception_type': misc.get('type', 'unknown'),
                            'severity': misc.get('severity', 3)
                        }
                        profile_data['error_patterns'].append(error_episode)
                        
                        # Create ErrorEpisode in Neo4j
                        await self._create_error_episode(learner_id, error_episode)
                
                # 4. Estimate & update Bloom's level
                bloom_level = self._estimate_bloom_level(
                    score=score,
                    difficulty=question_difficulty,
                    question_type=question_type
                )
                
                if 'mastery_progression' not in profile_data:
                    profile_data['mastery_progression'] = {}
                profile_data['mastery_progression'][concept_id] = {
                    'timestamp': datetime.now().isoformat(),
                    'bloom_level': bloom_level,
                    'score': score,
                    'difficulty': question_difficulty
                }
                
                # 5. Recalculate avg_mastery_level (dim 15)
                mastery_values = list(profile_data['concept_mastery_map'].values())
                profile_data['avg_mastery_level'] = (
                    sum(mastery_values) / len(mastery_values)
                    if mastery_values else 0.0
                )
                
                # 6. Update metadata with optimistic locking
                profile_data['version'] = version_before + 1
                profile_data['last_updated'] = datetime.now().isoformat()
                profile_data['last_updated_by'] = 'profiler'
                
                await redis.set(f"profile:{learner_id}", profile_data, ttl=1800)
                
                # 7. Selective publish: only if avg_mastery changed > 10%
                mastery_change = abs(profile_data['avg_mastery_level'] - prev_avg_mastery)
                if mastery_change > 0.1:
                    await self.send_message(
                        receiver="planner",
                        message_type="PROFILE_ADVANCED",
                        payload={
                            'learner_id': learner_id,
                            'new_avg_mastery': profile_data['avg_mastery_level']
                        }
                    )
                
                self.logger.info({
                    'event': 'profile_updated_evaluation',
                    'learner_id': learner_id,
                    'concept_id': concept_id,
                    'new_score': score,
                    'new_bloom': bloom_level
                })
                
            except Exception as e:
                self.logger.error(f"Error in _on_evaluation_completed: {e}")
    
    async def _on_pace_check(self, event: Dict[str, Any]):
        """Update learning_velocity when pace check triggered"""
        learner_id = event.get('learner_id')
        if not learner_id:
            return
        
        async with self._get_learner_lock(learner_id):
            try:
                pace_ratio = event.get('pace_ratio', 1.0)
                hours_spent = event.get('hours_spent', 1.0)
                
                redis = self.state_manager.redis
                profile_data = await redis.get(f"profile:{learner_id}")
                
                if not profile_data:
                    return
                
                # 1. Update learning_velocity (dim 16)
                concepts_done = len(profile_data.get('completed_concepts', []))
                profile_data['learning_velocity'] = (
                    concepts_done / hours_spent if hours_spent > 0 else 0.0
                )
                
                # 2. Auto-adjust difficulty preference
                if 'preferences' not in profile_data:
                    profile_data['preferences'] = {}
                
                if pace_ratio > 1.2:  # Ahead
                    profile_data['preferences']['difficulty_next'] = "HARD"
                elif pace_ratio < 0.8:  # Behind
                    profile_data['preferences']['difficulty_next'] = "EASY"
                else:
                    profile_data['preferences']['difficulty_next'] = "MEDIUM"
                
                # 3. Save
                profile_data['version'] = profile_data.get('version', 0) + 1
                profile_data['last_updated'] = datetime.now().isoformat()
                await redis.set(f"profile:{learner_id}", profile_data, ttl=1800)
                
                # 4. Publish if velocity anomaly
                if abs(profile_data['learning_velocity'] - 1.0) > 0.3:
                    event_type = 'LEARNER_ACCELERATING' if profile_data['learning_velocity'] > 1.0 else 'LEARNER_SLOWING'
                    await self.send_message(
                        receiver="planner",
                        message_type=event_type,
                        payload={'learner_id': learner_id, 'velocity': profile_data['learning_velocity']}
                    )
                
            except Exception as e:
                self.logger.error(f"Error in _on_pace_check: {e}")
    
    async def _on_artifact_created(self, event: Dict[str, Any]):
        """Track generated notes in profile"""
        learner_id = event.get('learner_id')
        if not learner_id:
            return
        
        async with self._get_learner_lock(learner_id):
            try:
                artifact_id = event['artifact_id']
                concept_id = event.get('concept_id', '')
                
                redis = self.state_manager.redis
                profile_data = await redis.get(f"profile:{learner_id}")
                
                if not profile_data:
                    return
                
                # 1. Add artifact ID (dim 14)
                if 'artifact_ids' not in profile_data:
                    profile_data['artifact_ids'] = []
                profile_data['artifact_ids'].append(artifact_id)
                
                # 2. Create ArtifactEpisode in Neo4j
                await self._create_artifact_episode(learner_id, {
                    'artifact_id': artifact_id,
                    'concept_id': concept_id,
                    'created_at': datetime.now().isoformat()
                })
                
                # 3. Save
                profile_data['version'] = profile_data.get('version', 0) + 1
                await redis.set(f"profile:{learner_id}", profile_data, ttl=1800)
                
            except Exception as e:
                self.logger.error(f"Error in _on_artifact_created: {e}")
    
    async def _on_kg_sync_completed(self, event: Dict[str, Any]):
        """
        Handle KG_SYNC_COMPLETED event from KAG Agent.
        
        Updates profile to reflect KG sync status.
        
        Event payload:
        {
            'learner_id': str,
            'sync_count': int,
            'timestamp': str
        }
        """
        learner_id = event.get('learner_id')
        if not learner_id:
            return
        
        async with self._get_learner_lock(learner_id):
            try:
                sync_count = event.get('sync_count', 0)
                timestamp = event.get('timestamp', datetime.now().isoformat())
                
                redis = self.state_manager.redis
                profile_data = await redis.get(f"profile:{learner_id}")
                
                if not profile_data:
                    return
                
                # Update KG sync tracking
                if 'kg_sync_history' not in profile_data:
                    profile_data['kg_sync_history'] = []
                
                profile_data['kg_sync_history'].append({
                    'sync_count': sync_count,
                    'timestamp': timestamp
                })
                
                # Keep only last 50 sync records
                profile_data['kg_sync_history'] = profile_data['kg_sync_history'][-50:]
                
                # Update last sync timestamp
                profile_data['last_kg_sync'] = timestamp
                
                # Save
                profile_data['version'] = profile_data.get('version', 0) + 1
                await redis.set(f"profile:{learner_id}", profile_data, ttl=1800)
                
                self.logger.debug(f"KG sync recorded for {learner_id}: {sync_count} items")
                
            except Exception as e:
                self.logger.error(f"Error in _on_kg_sync_completed: {e}")
    
    async def _on_artifact_generation_failed(self, event: Dict[str, Any]):
        """
        Handle ARTIFACT_GENERATION_FAILED event from KAG Agent.
        
        Tracks failed artifact generation attempts in profile.
        
        Event payload:
        {
            'learner_id': str,
            'concept_id': str,
            'reason': str
        }
        """
        learner_id = event.get('learner_id')
        if not learner_id:
            return
        
        async with self._get_learner_lock(learner_id):
            try:
                concept_id = event.get('concept_id', 'unknown')
                reason = event.get('reason', 'Unknown error')
                
                redis = self.state_manager.redis
                profile_data = await redis.get(f"profile:{learner_id}")
                
                if not profile_data:
                    return
                
                # Track failed generations
                if 'artifact_failures' not in profile_data:
                    profile_data['artifact_failures'] = []
                
                profile_data['artifact_failures'].append({
                    'concept_id': concept_id,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Keep only last 20 failure records
                profile_data['artifact_failures'] = profile_data['artifact_failures'][-20:]
                
                # Save
                profile_data['version'] = profile_data.get('version', 0) + 1
                await redis.set(f"profile:{learner_id}", profile_data, ttl=1800)
                
                self.logger.warning(f"Artifact generation failed for {learner_id}/{concept_id}: {reason}")
                
            except Exception as e:
                self.logger.error(f"Error in _on_artifact_generation_failed: {e}")
    
    def _estimate_bloom_level(self, score: float, difficulty: int, question_type: str) -> str:
        """
        Estimate Bloom's level from 3 signals (per handoff doc).
        
        Weights: score (60%) + difficulty (25%) + question_type (15%)
        """
        # Signal 1: Score-based (60% weight)
        if score < 0.2:
            bloom_from_score = 1
        elif score < 0.4:
            bloom_from_score = 2
        elif score < 0.6:
            bloom_from_score = 3
        elif score < 0.8:
            bloom_from_score = 4
        elif score < 0.9:
            bloom_from_score = 5
        else:
            bloom_from_score = 6
        
        # Signal 2: Difficulty adjustment (25% weight)
        difficulty_adjustment = -0.5 if difficulty >= 4 else (0.5 if difficulty <= 2 else 0)
        
        # Signal 3: Question type (15% weight)
        question_boost = {
            'factual': 0, 
            'conceptual': 0.3, 
            'application': 0.7, 
            'synthesis': 1.0
        }.get(question_type, 0)
        
        # Combine signals
        combined = (
            0.60 * bloom_from_score +
            0.25 * (bloom_from_score + difficulty_adjustment) +
            0.15 * (bloom_from_score + question_boost)
        )
        
        # Round to Bloom level
        final_idx = round(min(6, max(1, combined)))
        bloom_levels = ["", "REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"]
        return bloom_levels[final_idx]

    def _apply_interest_decay(self, profile_data: Dict[str, Any], decay_rate: float = 0.95):
        """
        Mechanism 3: Dynamic Interest Decay.
        Apply time-decay factor to interest_tags.
        Remove tags that fall below threshold (0.1).
        """
        if 'interest_tags' in profile_data:
            tags = profile_data['interest_tags']
            to_remove = []
            
            for tag in tags:
                tags[tag] *= decay_rate
                if tags[tag] < 0.1:
                    to_remove.append(tag)
            
            for tag in to_remove:
                del tags[tag]
            
            profile_data['interest_tags'] = tags
    
    async def _create_error_episode(self, learner_id: str, error_data: Dict):
        """Create ErrorEpisode node in Neo4j Personal KG"""
        try:
            neo4j = self.state_manager.neo4j
            await neo4j.run_query(
                """
                MATCH (l:Learner {learner_id: $learner_id})
                CREATE (e:ErrorEpisode {
                    error_id: $error_id,
                    concept_id: $concept_id,
                    misconception_type: $misconception_type,
                    severity: $severity,
                    timestamp: datetime()
                })
                CREATE (l)-[:HAS_ERROR]->(e)
                """,
                learner_id=learner_id,
                error_id=error_data['error_id'],
                concept_id=error_data['concept_id'],
                misconception_type=error_data['misconception_type'],
                severity=error_data['severity']
            )
        except Exception as e:
            self.logger.error(f"Failed to create ErrorEpisode: {e}")
    
    async def _create_artifact_episode(self, learner_id: str, artifact_data: Dict):
        """Create ArtifactEpisode node in Neo4j Personal KG"""
        try:
            neo4j = self.state_manager.neo4j
            await neo4j.run_query(
                """
                MATCH (l:Learner {learner_id: $learner_id})
                CREATE (a:ArtifactEpisode {
                    artifact_id: $artifact_id,
                    concept_id: $concept_id,
                    created_at: datetime()
                })
                CREATE (l)-[:HAS_ARTIFACT]->(a)
                """,
                learner_id=learner_id,
                artifact_id=artifact_data['artifact_id'],
                concept_id=artifact_data['concept_id']
            )
        except Exception as e:
            self.logger.error(f"Failed to create ArtifactEpisode: {e}")
