from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.rl_engine import RLEngine, BanditStrategy
from backend.core.constants import (
    CHAIN_RELATIONSHIPS,
    MASTERY_PROCEED_THRESHOLD,
    MASTERY_PREREQUISITE_THRESHOLD,
    CONCEPT_BASE_TIME,
    DIFFICULTY_MULTIPLIER,
    TIME_BUDGET_FACTOR,
    MAX_PATH_CONCEPTS,
    PACING_AGGRESSIVE_THRESHOLD,
    PACING_MODERATE_THRESHOLD,
    SUCCESS_PROB_MASTERY_WEIGHT,
    SUCCESS_PROB_TIME_WEIGHT,
    SUCCESS_PROB_DIFFICULTY_WEIGHT,
    # Fix 2: Import Config Constants
    GATE_FULL_PASS_SCORE,
    REVIEW_CHANCE
)
from backend.models import LearnerProfile
from backend.config import get_settings
import random  # Explicit import for cleaner usage
import asyncio # For lock handling

logger = logging.getLogger(__name__)


class ChainingMode(str, Enum):
    """Adaptive Sequencing Modes per THESIS Section 3.1.2"""
    FORWARD = "FORWARD"    # Success -> NEXT, IS_PREREQUISITE_OF
    BACKWARD = "BACKWARD"  # Remediate -> REQUIRES (go to prerequisites)
    LATERAL = "LATERAL"    # Stuck -> SIMILAR_TO, HAS_ALTERNATIVE_PATH, REMEDIATES
    ACCELERATE = "ACCELERATE"  # Flow State -> NEXT (harder), IS_SUB_CONCEPT_OF
    REVIEW = "REVIEW"      # Spaced Repetition -> REQUIRES (review old concepts)


class EvaluationDecision(str, Enum):
    """From Evaluator Agent (Agent 5)"""
    PROCEED = "PROCEED"      # Score >= 0.8, move forward
    MASTERED = "MASTERED"    # Perfect score, skip to next
    REMEDIATE = "REMEDIATE"  # Score < 0.3, go backward
    ALTERNATE = "ALTERNATE"  # Different approach needed
    RETRY = "RETRY"          # Try again with same concept


class PathPlannerAgent(BaseAgent):
    """
    Path Planner Agent - Generate optimal learning sequence using RL.
    
    Features (per Thesis):
    1. Multi-Armed Bandit with UCB (exploitation + exploration)
    2. Adaptive Sequencing with 3 Chaining Modes:
       - Forward: Success -> move to NEXT or IS_PREREQUISITE_OF concepts
       - Backward: Fail -> go to REQUIRES (prerequisites)
       - Lateral: Stuck -> try SIMILAR_TO or HAS_ALTERNATIVE_PATH
    3. Prerequisite validation (hard constraint)
    4. Success probability calculation
    
    Process Flow:
    1. Get learner profile + Course KG
    2. Initialize RL engine with all concepts
    3. Build prerequisite + relationship maps
    4. Generate path using adaptive chaining
    5. Recommend resources
    6. Calculate success probability
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        super().__init__(agent_id, AgentType.PATH_PLANNER, state_manager, event_bus)
        
        self.settings = get_settings()
        # UPGRADE: Use LinUCB (Contextual Bandit) instead of basic UCB
        self.rl_engine = RLEngine(strategy=BanditStrategy.LINUCB)
        self.logger = logging.getLogger(f"PathPlannerAgent.{agent_id}")
        
        # Relationship type priorities for each chaining mode
        self.CHAIN_RELATIONSHIPS = {
            ChainingMode.FORWARD: ["NEXT", "IS_PREREQUISITE_OF"],
            ChainingMode.BACKWARD: ["REQUIRES"],
            ChainingMode.LATERAL: ["SIMILAR_TO", "HAS_ALTERNATIVE_PATH", "REMEDIATES"],
            ChainingMode.ACCELERATE: ["NEXT", "IS_SUB_CONCEPT_OF"],
            ChainingMode.REVIEW: ["REQUIRES"]  # Logic uses this to find prior nodes
        }
        
        self._subscribe_to_events()
        
    def _subscribe_to_events(self):
        """Subscribe to feedback events"""
        if hasattr(self.event_bus, 'subscribe'):
            self.event_bus.subscribe("EVALUATION_COMPLETED", self._on_evaluation_feedback)
            self.logger.info("Subscribed to EVALUATION_COMPLETED")

    async def _load_mab_stats(self, concept_ids: List[str]):
        """Load MAB stats from Redis for relevant concepts"""
        redis = self.state_manager.redis
        pipeline = redis.pipeline()
        
        for cid in concept_ids:
            pipeline.get(f"mab_stats:{cid}")
            
        results = await pipeline.execute()
        
        for cid, data_str in zip(concept_ids, results):
            if data_str:
                try:
                    data = json.loads(data_str)
                    if cid in self.rl_engine.arms:
                        self.rl_engine.arms[cid].set_stats(
                            pulls=data.get("pulls", 0),
                            total_reward=data.get("total_reward", 0.0)
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to load MAB stats for {cid}: {e}")

    async def _save_mab_stats(self, concept_ids: List[str]):
        """Save MAB stats to Redis"""
        redis = self.state_manager.redis
        pipeline = redis.pipeline()
        
        for cid in concept_ids:
            if cid in self.rl_engine.arms:
                arm = self.rl_engine.arms[cid]
                data = {
                    "pulls": arm.pulls,
                    "total_reward": arm.total_reward
                }
                pipeline.set(f"mab_stats:{cid}", json.dumps(data))
                
        await pipeline.execute()
    
    async def _load_linucb_arms(self, concept_ids: List[str]):
        """Load LinUCB arm state from Redis (Ridge Regression matrices)."""
        from backend.core.rl_engine import LinUCBArm
        
        redis = self.state_manager.redis
        pipeline = redis.pipeline()
        
        for cid in concept_ids:
            pipeline.get(f"linucb:{cid}")
        
        results = await pipeline.execute()
        
        for cid, data_str in zip(concept_ids, results):
            if data_str:
                try:
                    data = json.loads(data_str)
                    arm = LinUCBArm.from_dict(data)
                    self.rl_engine.linucb_arms[cid] = arm
                    self.logger.debug(f"Loaded LinUCB state for {cid} (pulls={arm.pulls})")
                except Exception as e:
                    self.logger.warning(f"Failed to load LinUCB state for {cid}: {e}")
    
    async def _save_linucb_arms(self, concept_ids: List[str]):
        """Save LinUCB arm state to Redis."""
        redis = self.state_manager.redis
        pipeline = redis.pipeline()
        
        for cid in concept_ids:
            if cid in self.rl_engine.linucb_arms:
                arm = self.rl_engine.linucb_arms[cid]
                pipeline.set(f"linucb:{cid}", json.dumps(arm.to_dict()))
        
        await pipeline.execute()
        self.logger.info(f"Saved LinUCB state for {len(concept_ids)} concepts")

    async def _on_evaluation_feedback(self, event: Dict[str, Any]):
        """
        Process feedback from Evaluator Agent.
        R = 0.6 * score + 0.4 * completion - penalty
        
        Improvements:
        - Loads LinUCB arm from Redis if not in memory (Issue 1)
        - Loads context_vector from Redis if not in event (Issue 2)
        - Syncs in-memory MAB state after Redis update (Issue 3)
        - Includes retry mechanism for Redis (Issue 5)
        """
        MAX_RETRIES = 3
        
        try:
            concept_id = event.get('concept_id')
            score = event.get('score', 0.0)
            passed = event.get('passed', score >= MASTERY_PROCEED_THRESHOLD)
            
            if not concept_id:
                return
            
            # Fix 1: Distributed Lock (Gap 1)
            # Lock by concept_id to protect LinUCB global state
            redis_lock = self.state_manager.redis.lock(name=f"lock:concept:{concept_id}", timeout=5)
            acquired = False
            try:
                if asyncio.iscoroutinefunction(redis_lock.acquire):
                    acquired = await redis_lock.acquire()
                else:
                    acquired = redis_lock.acquire()
            except:
                acquired = False

            if not acquired:
                self.logger.warning(f"Could not acquire lock for concept {concept_id}, skipping feedback update.")
                return

            try:
                # Calculate Reward
                completion_reward = 1.0 if passed else 0.0
                dropout_penalty = 0.0  # TODO: detect dropout from behavior signals
                
                reward = (0.6 * score) + (0.4 * completion_reward) - dropout_penalty
                
                # --- UPDATE MAB STATS (with retry) ---
                redis = self.state_manager.redis
                key = f"mab_stats:{concept_id}"
                
                for attempt in range(MAX_RETRIES):
                    try:
                        data_str = await redis.get(key)
                        
                        if data_str:
                            data = json.loads(data_str)
                            pulls = data.get("pulls", 0) + 1
                            total_reward = data.get("total_reward", 0.0) + reward
                        else:
                            pulls = 1
                            total_reward = reward
                            
                        await redis.set(key, json.dumps({
                            "pulls": pulls,
                            "total_reward": total_reward
                        }))
                        
                        # FIX Issue 3: Sync in-memory MAB state
                        if concept_id in self.rl_engine.arms:
                            self.rl_engine.arms[concept_id].set_stats(pulls, total_reward)
                        
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        if attempt == MAX_RETRIES - 1:
                            self.logger.error(f"Redis update failed after {MAX_RETRIES} attempts: {e}")
                            raise
                        await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
                
                # --- UPDATE LINUCB ARM STATE ---
                # FIX Issue 2: Load context from Redis if not in event
                context_vector = event.get('context_vector')
                if not context_vector:
                    # Try to load from saved selection context
                    context_key = f"linucb_context:{concept_id}"
                    context_str = await redis.get(context_key)
                    if context_str:
                        context_vector = json.loads(context_str)
                        self.logger.debug(f"Loaded context_vector from Redis for {concept_id}")
                
                if context_vector:
                    # FIX Issue 1: Load LinUCB arm from Redis if not in memory
                    if concept_id not in self.rl_engine.linucb_arms:
                        await self._load_linucb_arms([concept_id])
                        self.logger.debug(f"Loaded LinUCB arm from Redis for {concept_id}")
                    
                    # Now update the arm (create new if still doesn't exist)
                    if concept_id not in self.rl_engine.linucb_arms:
                        from backend.core.rl_engine import LinUCBArm
                        self.rl_engine.linucb_arms[concept_id] = LinUCBArm(
                            concept_id, d=self.rl_engine.context_dim
                        )
                    
                    arm = self.rl_engine.linucb_arms[concept_id]
                    arm.update(context_vector, reward)
                    await self._save_linucb_arms([concept_id])
                    self.logger.info(f"LinUCB arm updated for {concept_id}")
                else:
                    self.logger.warning(f"No context_vector available for LinUCB update on {concept_id}")
                
                self.logger.info(f"Feedback processed for {concept_id}: Reward={reward:.2f}")

            finally:
                if acquired:
                    try: await redis_lock.release()
                    except: pass
            
        except Exception as e:
            self.logger.error(f"Error processing feedback: {e}")
        

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Main execution method."""
        try:
            learner_id = kwargs.get("learner_id")
            goal = kwargs.get("goal")
            last_result = kwargs.get("last_result")  # From evaluator
            
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
            
            # Step 2: Get Course KG (SMART FILTERING - use Personal Subgraph)
            neo4j = self.state_manager.neo4j
            topic = learner_profile.get("topic", "")
            
            # Strategy 1: Start from learner's MasteryNodes, expand to connected concepts
            course_concepts = await neo4j.run_query(
                """
                // Find concepts the learner already knows (via MasteryNodes)
                OPTIONAL MATCH (l:Learner {learner_id: $learner_id})-[:HAS_MASTERY]->(m:MasteryNode)-[:MAPS_TO_CONCEPT]->(known:CourseConcept)
                WITH collect(known) as known_concepts
                
                // Expand to connected concepts (neighbors)
                MATCH (c:CourseConcept)
                WHERE c IN known_concepts 
                   OR EXISTS { (c)-[:NEXT|REQUIRES|SIMILAR_TO|IS_PREREQUISITE_OF]->(:CourseConcept) WHERE (c)-[:NEXT|REQUIRES|SIMILAR_TO|IS_PREREQUISITE_OF]->(known_concepts[0]) }
                   OR (size(known_concepts) = 0 AND (toLower(c.name) CONTAINS toLower($topic) OR any(tag IN coalesce(c.semantic_tags, []) WHERE toLower(tag) CONTAINS toLower($topic))))
                RETURN DISTINCT c.concept_id as concept_id, 
                       c.name as name, 
                       c.difficulty as difficulty,
                       c.time_estimate as time_estimate
                LIMIT 100
                """,
                learner_id=learner_id,
                topic=topic
            )
            
            # Fallback: If still no concepts, get most central concepts related to topic
            if not course_concepts:
                self.logger.warning(f"No concepts found via Personal KG, falling back to centrality-based selection for topic: {topic}")
                course_concepts = await neo4j.run_query(
                    """
                    MATCH (c:CourseConcept)
                    WHERE toLower(c.name) CONTAINS toLower($topic)
                       OR any(tag IN coalesce(c.semantic_tags, []) WHERE toLower(tag) CONTAINS toLower($topic))
                    WITH c, size((c)-[:REQUIRES]->()) + size((c)<-[:REQUIRES]-()) as centrality
                    ORDER BY centrality DESC
                    LIMIT 50
                    RETURN c.concept_id as concept_id, c.name as name, c.difficulty as difficulty, c.time_estimate as time_estimate
                    """,
                    topic=topic
                )
            
            # Get ALL relationship types for the selected concepts
            concept_ids = [c['concept_id'] for c in course_concepts]
            course_relationships = await neo4j.run_query(
                """
                MATCH (a:CourseConcept)-[r]->(b:CourseConcept)
                WHERE a.concept_id IN $concept_ids AND b.concept_id IN $concept_ids
                RETURN a.concept_id as source, 
                       b.concept_id as target,
                       type(r) as rel_type
                """,
                concept_ids=concept_ids
            )
            
            if not course_concepts:
                return {
                    "success": False,
                    "error": "No concepts found in Course KG",
                    "agent_id": self.agent_id
                }
            
            # Step 3: Initialize RL engine
            for concept in course_concepts:
                self.rl_engine.add_arm(
                    concept['concept_id'],
                    concept.get('difficulty', 2)
                )
            
            # Step 4: Build relationship maps (for all 7 types)
            relationship_map = self._build_relationship_map(course_relationships)
            prerequisites = relationship_map.get("REQUIRES", {})
            
            # Step 5: Determine chaining mode
            chain_mode = self._select_chain_mode(last_result)
            
            # Step 6: Generate learning path with adaptive chaining
            learning_path = await self._generate_adaptive_path(
                learner_profile=learner_profile,
                course_concepts=course_concepts,
                relationship_map=relationship_map,
                chain_mode=chain_mode
            )
            
            if not learning_path["success"]:
                return learning_path
            
            # Step 7: Recommend resources
            resources = await self._recommend_resources(
                learning_path["path"],
                learner_profile
            )
            
            # Step 8: Calculate success probability (with live mastery data)
            success_prob = await self._calculate_success_probability(
                learner_profile,
                learning_path["path"],
                learning_path.get("current_mastery", {})  # FIX: Use live mastery
            )
            
            result = {
                "success": True,
                "agent_id": self.agent_id,
                "learner_id": learner_id,
                "chain_mode": chain_mode.value,
                "learning_path": learning_path["path"],
                "pacing": learning_path["pacing"],
                "success_probability": success_prob,
                "total_estimated_hours": learning_path["total_hours"],
                "resources": resources
            }
            
            # Save path to state
            await self.save_state(f"path:{learner_id}", result)
            
            # Emit event for tutor
            await self.send_message(
                receiver="tutor",
                message_type="path_planned",
                payload={
                    "learner_id": learner_id,
                    "first_concept": learning_path["path"][0]["concept"] if learning_path["path"] else None,
                    "total_concepts": len(learning_path["path"]),
                    "chain_mode": chain_mode.value
                }
            )
            
            self.logger.info(f"✅ Learning path generated: {len(learning_path['path'])} concepts ({chain_mode.value} mode)")
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ Path planning failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    def _build_relationship_map(self, relationships: List[Dict]) -> Dict[str, Dict[str, List[str]]]:
        """Build relationship map organized by type"""
        rel_map = {}
        
        for rel in relationships:
            rel_type = rel.get("rel_type", "REQUIRES")
            source = rel["source"]
            target = rel["target"]
            
            if rel_type not in rel_map:
                rel_map[rel_type] = {}
            
            if source not in rel_map[rel_type]:
                rel_map[rel_type][source] = []
            
            rel_map[rel_type][source].append(target)
        
        return rel_map
    
    def _select_chain_mode(self, last_result: Optional[str]) -> ChainingMode:
        """
        Select chaining mode based on last evaluation result.
        
        - MASTERED -> ACCELERATE (Flow State)
        - PROCEED -> FORWARD (Normal progression)
        - REMEDIATE -> BACKWARD (Prerequisites)
        - ALTERNATE/RETRY -> LATERAL (Different approach)
        - None (Start of session) -> Check for REVIEW needs
        """
        if last_result == "MASTERED":
            return ChainingMode.ACCELERATE
        elif last_result == "PROCEED":
            return ChainingMode.FORWARD
        elif last_result == "REMEDIATE":
            return ChainingMode.BACKWARD
        elif last_result in ["ALTERNATE", "RETRY"]:
            return ChainingMode.LATERAL
        else:
            # Start of session or unknown state
            # Simple heuristic: 10% chance to trigger REVIEW mode for Spaced Repetition
            # In production, this would check 'last_reviewed_at' decay
            if random.random() < REVIEW_CHANCE:
                return ChainingMode.REVIEW
            return ChainingMode.FORWARD
    
    async def _generate_adaptive_path(
        self,
        learner_profile: Dict[str, Any],
        course_concepts: List[Dict[str, Any]],
        relationship_map: Dict[str, Dict[str, List[str]]],
        chain_mode: ChainingMode
    ) -> Dict[str, Any]:
        """Generate path using adaptive chaining strategy"""
        try:
            path = []
            current_mastery = {
                m["concept_id"]: m["mastery_level"]
                for m in learner_profile.get("current_mastery", [])
            }
            
            time_available = learner_profile.get("time_available", 30)
            hours_per_day = learner_profile.get("hours_per_day", 2)
            total_hours = time_available * hours_per_day
            hours_used = 0
            day = 1
            
            # Get relevant relationship types for current mode
            relevant_rel_types = self.CHAIN_RELATIONSHIPS[chain_mode]
            prerequisites = relationship_map.get("REQUIRES", {})
            
            # --- PROBABILISTIC MASTERY GATE (Scientific Upgrade) ---
            # Replace hard 0.8 threshold with soft probabilistic gate
            # Allows occasional exploration even at lower scores
            if path:
                last_concept_id = path[-1]["concept"]
            else:
                last_concept_id = None

            if last_concept_id:
                current_score = current_mastery.get(last_concept_id, 0.0)
                
                # Probabilistic Gate: gate_prob = min(1.0, score / 0.8)
                # At score 0.8+: 100% pass. At 0.6: 75% pass. At 0.4: 50% pass.
                gate_prob = min(1.0, current_score / GATE_FULL_PASS_SCORE)
                
                if random.random() > gate_prob:
                    # Block forward progress with probability (1 - gate_prob)
                    self.logger.info(f"🎲 PROBABILISTIC GATE: Score={current_score:.2f}, GateProb={gate_prob:.2f} -> Forcing remediation")
                    if chain_mode not in [ChainingMode.BACKWARD, ChainingMode.LATERAL, ChainingMode.REVIEW]:
                        chain_mode = ChainingMode.BACKWARD
                        relevant_rel_types = self.CHAIN_RELATIONSHIPS[ChainingMode.BACKWARD]
                else:
                    self.logger.debug(f"✅ PROBABILISTIC GATE: Score={current_score:.2f}, GateProb={gate_prob:.2f} -> Allowed to proceed")
            # -------------------------------------

            visited = set()
            
            while hours_used < total_hours * 0.8:
                # Get candidates based on chaining mode
                candidates = self._get_chain_candidates(
                    current_concept=path[-1]["concept"] if path else None,
                    relationship_map=relationship_map,
                    relevant_rel_types=relevant_rel_types,
                    course_concepts=course_concepts,
                    visited=visited,
                    current_mastery=current_mastery,
                    prerequisites=prerequisites,
                    chain_mode=chain_mode
                )
                
                if not candidates:
                    # Try lateral mode if stuck
                    if chain_mode != ChainingMode.LATERAL:
                        candidates = self._get_chain_candidates(
                            current_concept=path[-1]["concept"] if path else None,
                            relationship_map=relationship_map,
                            relevant_rel_types=self.CHAIN_RELATIONSHIPS[ChainingMode.LATERAL],
                            course_concepts=course_concepts,
                            visited=visited,
                            current_mastery=current_mastery,
                            prerequisites=prerequisites,
                            chain_mode=ChainingMode.LATERAL
                        )
                    
                    if not candidates:
                        break
                
                # LOAD MAB STATS FOR CANDIDATES (Stateful Bandit)
                await self._load_mab_stats(candidates)
                
                # LOAD LINUCB STATE FOR CANDIDATES (Persistent Ridge Regression)
                await self._load_linucb_arms(candidates)
                
                # Get profile vector for LinUCB (context-aware selection)
                profile_vector = learner_profile.get("profile_vector", [0.0] * 10)
                
                # Build time estimates map for candidates (FIX Issue 3)
                concept_time_estimates = {}
                for c in course_concepts:
                    cid = c.get("concept_id")
                    if cid in candidates:
                        diff = c.get("difficulty", 2)
                        concept_time_estimates[cid] = c.get("time_estimate", diff * 30) / 60
                
                # Use RL to select from candidates (LinUCB with context + time filter)
                next_concept = self.rl_engine.select_concept(
                    learner_mastery=current_mastery,
                    prerequisites=prerequisites,
                    time_available=int(total_hours - hours_used),
                    learning_style=learner_profile.get("preferred_learning_style", "VISUAL"),
                    candidate_concepts=candidates,
                    context_vector=profile_vector,
                    concept_time_estimates=concept_time_estimates  # NEW: Time filtering
                )
                
                if not next_concept:
                    break
                
                # Get concept details
                concept = next(
                    (c for c in course_concepts if c['concept_id'] == next_concept),
                    None
                )
                if not concept:
                    visited.add(next_concept)
                    continue
                
                # Calculate estimated hours
                difficulty = concept.get('difficulty', 2)
                time_estimate = concept.get('time_estimate', difficulty * 30) / 60  # Convert to hours
                
                if hours_used + time_estimate > total_hours:
                    break
                
                # Add to path
                path.append({
                    "day": day,
                    "concept": next_concept,
                    "concept_name": concept.get('name', next_concept),
                    "difficulty": difficulty,
                    "estimated_hours": round(time_estimate, 1),
                    "chain_mode": chain_mode.value,
                    "recommended_type": self._recommend_content_type(
                        difficulty,
                        learner_profile.get("preferred_learning_style", "VISUAL")
                    )
                })
                
                # Update tracking
                visited.add(next_concept)
                hours_used += time_estimate
                # FIX Issue 4: Calculate initial mastery based on difficulty
                # Harder concepts start with lower mastery expectation
                initial_mastery = max(0.1, 0.5 - (difficulty * 0.08))
                current_mastery[next_concept] = initial_mastery
                day = int(hours_used / hours_per_day) + 1
                
                # FIX Feedback Issue 2: Save context_vector for this concept selection
                # So Feedback Loop can load it if not provided by Evaluator
                context_key = f"linucb_context:{next_concept}"
                await self.state_manager.redis.set(
                    context_key,
                    json.dumps(profile_vector),
                    ex=86400  # Expire after 24 hours
                )
            
            # Determine pacing
            pacing = self._determine_pacing(hours_used, total_hours, len(path))
            
            return {
                "success": True,
                "path": path,
                "pacing": pacing,
                "total_hours": round(hours_used, 1),
                "current_mastery": current_mastery  # FIX: Return live mastery for success_prob calc
            }
        
        except Exception as e:
            self.logger.error(f"Path generation error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_chain_candidates(
        self,
        current_concept: Optional[str],
        relationship_map: Dict[str, Dict[str, List[str]]],
        relevant_rel_types: List[str],
        course_concepts: List[Dict],
        visited: set,
        current_mastery: Dict[str, float],
        prerequisites: Dict[str, List[str]],
        chain_mode: ChainingMode = ChainingMode.FORWARD
    ) -> List[str]:
        """Get candidate concepts based on chaining mode relationships"""
        candidates = []
        
        if current_concept:
            # Special handling for ACCELERATE: Look ahead 2 steps for NEXT
            if chain_mode == ChainingMode.ACCELERATE:
                direct_next = relationship_map.get("NEXT", {}).get(current_concept, [])
                for next_c in direct_next:
                    candidates.append(next_c)
                    # Look one more step ahead (with prerequisite check)
                    second_step = relationship_map.get("NEXT", {}).get(next_c, [])
                    for step2 in second_step:
                        # FIX Issue 4: Check prerequisites for step 2
                        prereqs = prerequisites.get(step2, [])
                        prereqs_met = all(
                            current_mastery.get(p, 0) >= MASTERY_PREREQUISITE_THRESHOLD or p in visited
                            for p in prereqs
                        )
                        if prereqs_met:
                            candidates.append(step2)
                
                # Also include IS_SUB_CONCEPT_OF parent/child
                sub_concepts = relationship_map.get("IS_SUB_CONCEPT_OF", {}).get(current_concept, [])
                candidates.extend(sub_concepts)
            
            else:
                # Normal handling for FORWARD, BACKWARD, LATERAL, REVIEW
                for rel_type in relevant_rel_types:
                    if rel_type in relationship_map:
                        related = relationship_map[rel_type].get(current_concept, [])
                        candidates.extend(related)
        else:
            # No current concept (Cold-start)
            if chain_mode == ChainingMode.REVIEW:
                # FIX Issue 2: Proper Spaced Repetition with decay
                # Prioritize concepts with high mastery but not recently accessed
                # Simulate decay: older mastery = higher priority for review
                from datetime import datetime, timedelta
                
                review_candidates = []
                for cid, mastery in current_mastery.items():
                    if mastery > 0.7:  # Only review concepts with decent mastery
                        # TODO: In production, use actual last_accessed_at from DB
                        # For now, score based on mastery (lower = needs review more)
                        review_score = 1.0 - mastery + 0.2  # Add bonus for review
                        review_candidates.append((cid, review_score))
                
                # Sort by review priority (higher score = more urgent review)
                review_candidates.sort(key=lambda x: x[1], reverse=True)
                candidates = [c[0] for c in review_candidates[:10]]  # Top 10 for review
            
            else:
                # FIX Issue 3: Cold-start should return ROOT concepts (no prerequisites)
                # Not ALL concepts - that defeats Goal-Centric Filtering!
                root_concepts = []
                for c in course_concepts:
                    cid = c["concept_id"]
                    prereqs = prerequisites.get(cid, [])
                    if len(prereqs) == 0:  # No prerequisites = root concept
                        root_concepts.append(cid)
                
                if root_concepts:
                    candidates = root_concepts
                else:
                    # Fallback: lowest difficulty concepts
                    sorted_concepts = sorted(course_concepts, key=lambda x: x.get("difficulty", 2))
                    candidates = [c["concept_id"] for c in sorted_concepts[:10]]
        
        # Filter: not visited, prerequisites met
        valid_candidates = []
        for candidate in candidates:
            if candidate in visited:
                continue
            
            # FIX Issue 1: Unify prerequisites threshold to 0.7 (matches rl_engine.py)
            prereqs = prerequisites.get(candidate, [])
            prereqs_met = all(
                current_mastery.get(p, 0) >= 0.7 or p in visited
                for p in prereqs
            )
            
            if prereqs_met:
                valid_candidates.append(candidate)
        
        return list(set(valid_candidates))
    
    def _determine_pacing(self, hours_used: float, total_hours: float, path_length: int) -> str:
        """Determine pacing based on resource usage"""
        if path_length == 0:
            return "NO_PATH"
        elif hours_used > total_hours * 0.9:
            return "AGGRESSIVE"
        elif hours_used > total_hours * 0.7:
            return "MODERATE"
        else:
            return "RELAXED"
    
    async def _recommend_resources(
        self,
        learning_path: List[Dict[str, Any]],
        learner_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Recommend learning resources for each concept.
        
        TODO: In production, query actual resources from Content Management System
        or Knowledge Graph. Currently returns placeholder resource types.
        """
        resources = []
        learning_style = learner_profile.get("preferred_learning_style", "VISUAL")
        
        for step in learning_path:
            concept = step["concept"]
            difficulty = step.get("difficulty", 2)
            
            # Use _recommend_content_type for primary resource (consolidate logic)
            primary_type = self._recommend_content_type(difficulty, learning_style)
            
            resource = {
                "concept": concept,
                "primary_type": primary_type,  # Consolidated with path item's recommended_type
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
        learning_path: List[Dict[str, Any]],
        current_mastery: Optional[Dict[str, float]] = None  # FIX: Accept live mastery
    ) -> float:
        """
        Calculate probability of completing learning path.
        
        Formula (per THESIS Section 3.1.3):
        P(success) = 0.4 × avg_mastery + 0.4 × time_fit - 0.2 × difficulty_penalty
        """
        if not learning_path:
            return 0.0
        
        # Component 1: Average mastery (40%)
        # FIX: Use current_mastery (live) first, fallback to profile's concept_mastery_map
        mastery_source = current_mastery if current_mastery else learner_profile.get("concept_mastery_map", {})
        mastery_scores = [
            mastery_source.get(step['concept'], 0.0)
            for step in learning_path
        ]
        avg_mastery = sum(mastery_scores) / len(mastery_scores) if mastery_scores else 0.0
        
        # Component 2: Time fit (40%)
        total_hours = sum(s.get("estimated_hours", 0) for s in learning_path)
        
        # FIX: Align with Agent 2's Profile Schema (Days * Hours/Day)
        time_days = learner_profile.get("time_available", 30)
        hours_per_day = learner_profile.get("hours_per_day", 2)
        available_hours = time_days * hours_per_day
        
        time_fit = min(1.0, available_hours / total_hours) if total_hours > 0 else 1.0
        
        # Component 3: Difficulty penalty (20%) - penalty above medium difficulty
        avg_difficulty = sum(s.get("difficulty", 2) for s in learning_path) / len(learning_path)
        difficulty_penalty = max(0.0, (avg_difficulty - 3.0) * 0.1)
        
        # Combined with constants
        prob = (
            SUCCESS_PROB_MASTERY_WEIGHT * avg_mastery +
            SUCCESS_PROB_TIME_WEIGHT * time_fit -
            SUCCESS_PROB_DIFFICULTY_WEIGHT * difficulty_penalty
        )
        
        return max(0.0, min(1.0, prob))
    
    def _recommend_content_type(self, difficulty: int, learning_style: str) -> str:
        """Recommend content type based on difficulty and style"""
        if difficulty <= 2:
            return "TUTORIAL"
        elif difficulty <= 3:
            return "VIDEO" if learning_style == "VISUAL" else "ARTICLE"
        else:
            return "EXERCISE"
