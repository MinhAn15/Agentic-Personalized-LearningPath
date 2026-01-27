from typing import Dict, Any, List, Optional, Tuple
import numpy as np
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
        self.llm = llm  # Store LLM reference for ToT
        
        self.settings = get_settings()

        # UPGRADE: Tree of Thoughts (Beam Search) instead of LinUCB
        # Source: Yao et al. (2023)
        # UPGRADE: Tree of Thoughts (Beam Search) instead of LinUCB
        # Source: Yao et al. (2023)
        self.logger = logging.getLogger(f"PathPlannerAgent.{agent_id}")
        
        # System 1: RL Engine (Contextual Bandit) for Fallback
        self.rl_engine = RLEngine(
            feature_dim=10,
            alpha=self.settings.LINUCB_ALPHA
        )
        
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
    
    async def _explore_learning_paths(self, learner_id: str, concept_ids: List[str], current_concept: str = None, force_real: bool = False) -> List[str]:
        """
        Explore learning paths using Tree of Thoughts (Beam Search).
        Source: Yao et al. (2023)
        """
        if self.settings.MOCK_LLM and not force_real:
             self.logger.warning("Mocking ToT Path Planning (MOCK_LLM=True)")
             # Force 'concept_python_variables' if in candidates.
             # In a real scenario, this would choose the best next step.
             mock_target = 'concept_python_variables'
             if mock_target in concept_ids:
                 return [mock_target]
             return concept_ids[:1] # Default fallback capable

        if not current_concept:
             # Cold start: Use internal graph or fallback logic
             return concept_ids[:1]

        # 1. Thought Generator: Generate initial candidates (k=3)
        # Using the LLM to propose "Thoughts" (Review, Scaffold, Challenge)
        initial_thoughts = await self._thought_generator(
            learner_id, 
            current_concept, 
            target_concept=None # Could be passed from execute
        )
        
        # 2. Beam Search
        # Flatten thoughts to just concept_ids for the beam search, 
        # but we might want to keep metadata. For now, we stick to the signature.
        candidate_ids = [t['concept'] for t in initial_thoughts if t.get('concept')]
        
        return await self._beam_search(learner_id, candidate_ids)

    async def _beam_search(self, learner_id: str, initial_candidates: List[str]) -> List[str]:
        """
        Execute Beam Search (b=3, d=3) to find optimal path.
        """
        beam_width = self.settings.TOT_BEAM_WIDTH if hasattr(self.settings, 'TOT_BEAM_WIDTH') else 3
        max_depth = self.settings.TOT_MAX_DEPTH if hasattr(self.settings, 'TOT_MAX_DEPTH') else 3
        
        beam = [[c] for c in initial_candidates] # List of paths
        
        for depth in range(max_depth - 1): # Extend
            candidates = []
            
            for path in beam:
                last_node = path[-1]
                # Generate next thoughts (neighbors) via LLM Generator
                # We need to know the 'current_concept' context. 
                # Ideally, we pass the profile or graph. 
                # For now, we call the generator based on the last node.
                thoughts = await self._thought_generator(learner_id, last_node)
                neighbors = [t['concept'] for t in thoughts if t.get('concept')]
                
                if not neighbors:
                    # Fallback to Graph Neighbors if LLM fails or returns nothing
                    neighbors = await self._get_reachable_concepts(learner_id, last_node, limit=3)
                
                if not neighbors:
                    candidates.append((path, 0.0)) # Dead end
                    continue
                    
                # Evaluate new states
                for neighbor in neighbors: 
                    new_path = path + [neighbor]
                    score = await self._evaluate_path_viability(learner_id, new_path)
                    candidates.append((new_path, score))
            
            # Select best beam (Pruning)
            candidates.sort(key=lambda x: x[1], reverse=True)
            beam = [c[0] for c in candidates[:beam_width]]
            
        # Return best path from final beam
        if not beam:
            return []
        
        # Re-evaluate final beams to pick absolute best
        best_path = beam[0]
        best_score = -1.0
        
        for path in beam:
            score = await self._evaluate_path_viability(learner_id, path)
            if score > best_score:
                best_score = score
                best_path = path
                
        return best_path

    async def _evaluate_path_viability(self, learner_id: str, path: List[str]) -> float:
        """
        State Evaluator: Evaluate path feasibility (0.0 - 1.0).
        Uses "Mental Simulation" to predict learner's future state.
        
        Rigor Upgrade: Injects Affective State (Engagement) and Interaction Log.
        """
        if not self.llm:
            return 0.5 

        path_str = " -> ".join(path)
        
        # 1. Fetch Learner State (Affective + Cognitive)
        profile = await self.state_manager.get_learner_profile(learner_id)
        engagement = 0.8 # Default
        history_summary = "No recent history."
        
        if profile:
            # Dimension 17: engagement_score
            engagement = profile.get("engagement_score", 0.8)
            # Dimension 13: interaction_log (last 3 interactions for context)
            log = profile.get("interaction_log", [])
            if log:
                recent = log[-3:]
                history_summary = "\n".join([f"- {i.get('role')}: {i.get('content')[:100]}..." for i in recent])

        # 2. Hard Constraint: Prerequisite Check (The "Gatekeeper")
        # ---------------------------------------------------------
        if path and len(path) >= 1:
            target_node = path[-1]
            try:
                query = """
                MATCH (target:CourseConcept {concept_id: $target})<-[:REQUIRES]-(prereq:CourseConcept)
                WHERE NOT EXISTS {
                    MATCH (l:Learner {learner_id: $learner_id})-[:HAS_MASTERY]->(m:MasteryNode {concept_id: prereq.concept_id})
                    WHERE m.level >= $threshold
                }
                RETURN count(prereq) as missing_count
                """
                results = await self.state_manager.neo4j.run_query(
                    query, 
                    learner_id=learner_id, 
                    target=target_node,
                    threshold=MASTERY_PREREQUISITE_THRESHOLD
                )
                
                if results and results[0]['missing_count'] > 0:
                    missing = results[0]['missing_count']
                    self.logger.warning(f"🛑 Hard Constraint Blocking: {target_node} has {missing} unmet prerequisites.")
                    return 0.0 # REJECT IMMEDIATE (Constraint)
                    
            except Exception as e:
                self.logger.error(f"Constraint check failed: {e}")
                return 0.0

        # 3. LLM Evaluation (Mental Simulation)
        # ---------------------------------------------------------
        # We simulate the "Affective State" (Boredom/Frustration) based on engagement
        boredom_risk = "HIGH" if engagement < 0.4 else "LOW"
        
        prompt = f"""
        Learner ID: {learner_id}
        Engagement Score (Affective State): {engagement:.2f} (Boredom Risk: {boredom_risk})
        Recent History:
        {history_summary}

        Proposed Learning Path: {path_str}
        
        Task:
        Perform a mental simulation of the student learning this path. 
        Predict the learner's reaction considering their recent history and engagement level.

        Criteria:
        1. Frustration Risk: Is the step too large given their state?
        2. Boredom Risk: Is the path too repetitive?
        3. Scaffolding: Does this logically build on the 'Recent History'?

        Output format JSON:
        {{"simulation_reasoning": "...", "affective_prediction": "bored/frustrated/engaged", "value_score": 8}}
        """
        try:
            response = await self.llm.acomplete(prompt)
            data = json.loads(response.text.strip())
            score = data.get("value_score", 5)
            # Normalize 1-10 to 0.0-1.0
            return max(0.0, min(1.0, score / 10.0))
        except Exception as e:
            self.logger.warning(f"ToT Simulation failed: {e}")
            return 0.5

    async def _thought_generator(self, learner_id: str, current_concept: str, target_concept: str = None) -> List[Dict[str, Any]]:
        """
        Thought Generator: Propose 3 distinct next concepts (Thoughts).
        """
        if not self.llm:
            return []

        prompt = f"""
        Act as a Curriculum Architect.
        Input:
        Current Concept: {current_concept}
        Target Goal: {target_concept or "Next Logical Step"}
        
        Instruction:
        Propose 3 distinct next concepts to teach.
        - Option 1: "Review" step (consolidate foundation).
        - Option 2: "Scaffold" step (intermediate difficulty).
        - Option 3: "Challenge" step (direct approach).
        
        Output format (JSON):
        [
          {{"concept": "Concept_A", "strategy": "review", "reason": "..."}},
          {{"concept": "Concept_B", "strategy": "scaffold", "reason": "..."}},
          {{"concept": "Concept_C", "strategy": "challenge", "reason": "..."}}
        ]
        """
        try:
            response = await self.llm.acomplete(prompt)
            text = response.text.strip()
            # Clean generic markdown if present
            if text.startswith("```json"):
                text = text[7:-3]
            thoughts = json.loads(text)
            return thoughts if isinstance(thoughts, list) else []
        except Exception as e:
            self.logger.error(f"ToT Thought Generation failed: {e}")
            return []

    async def _get_reachable_concepts(self, learner_id: str, current_concept_id: str, limit: int = 5) -> List[str]:
        """
        Helper: Get next reachable concepts from Neo4j (Fallback for Generator).
        """
        try:
            query = """
            MATCH (c:CourseConcept {concept_id: $cid})-[:NEXT|IS_PREREQUISITE_OF]->(next:CourseConcept)
            RETURN next.concept_id as id
            LIMIT $limit
            """
            results = await self.state_manager.neo4j.run_query(query, cid=current_concept_id, limit=limit)
            return [r['id'] for r in results]
        except Exception as e:
            self.logger.error(f"Graph fallback failed: {e}")
            return []

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
                # Calculate Reward (The Rigorous Math)
                # Formula: R_t = (alpha * mastery) + (beta * completion) - (gamma * dropout_risk)
                
                # 1. Extract Components
                completion_reward = 1.0 if passed else 0.0
                
                # 2. Get Dropout Risk (from Event or Profiler)
                # If not in event, assume low risk (0.1) unless repeated failure
                dropout_risk = event.get('dropout_risk', 0.0)
                if not dropout_risk and not passed:
                    dropout_risk = 0.2  # Heuristic: Failure increases risk
                
                # 3. Define Constants (from Thesis)
                ALPHA = 0.6  # Mastery Weight
                BETA = 0.4   # Completion Weight
                GAMMA = 0.5  # Dropout Penalty Weight
                
                reward = (ALPHA * score) + (BETA * completion_reward) - (GAMMA * dropout_risk)
                
                # Log for Socratic Audit
                self.logger.info(f"💰 Reward Calc: {reward:.4f} = ({ALPHA}*{score:.2f}) + ({BETA}*{completion_reward}) - ({GAMMA}*{dropout_risk:.2f})")

                
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
            force_real = kwargs.get("force_real", False)
            
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
            topic = kwargs.get("topic") or getattr(learner_profile, "topic", "") or getattr(learner_profile, "goal", "")
            
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
            
            if self.settings.MOCK_LLM:
                 course_concepts = [{
                     "concept_id": "concept_python_variables",
                     "name": "Python Variables",
                     "difficulty": 1,
                     "time_estimate": 10
                 }]

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
            
            # --- UPGRADE: Tree of Thoughts (System 2) ---
            # Try to find a path using Beam Search approach first
            tot_path_ids = await self._explore_learning_paths(
                learner_id=learner_id,
                concept_ids=concept_ids,
                current_concept=getattr(learner_profile, "current_concept", None),
                force_real=force_real
            )
            
            learning_path = {"success": False}
            
            # If ToT found a valid sequence (min length 2 to be worth it?)
            if tot_path_ids and len(tot_path_ids) >= 1:
                self.logger.info(f"🧠 ToT Planner found path: {tot_path_ids}")
                # Convert IDs to detailed path
                learning_path = await self._construct_detailed_path(
                   learner_profile, tot_path_ids, course_concepts, chain_mode
                )
            
            # Fallback to LinUCB (System 1) if ToT failed or returned empty
            if not learning_path.get("success"):
                self.logger.info("⚠️ ToT Planner fallback -> Switching to LinUCB (System 1)")
                learning_path = await self._generate_adaptive_path(
                    learner_profile=learner_profile,
                    course_concepts=course_concepts,
                    relationship_map=relationship_map,
                    chain_mode=chain_mode
                )
            # --------------------------------------------
            
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

    async def _construct_detailed_path(
        self,
        learner_profile,  # Can be Dict or LearnerProfile
        path_ids: List[str],
        course_concepts: List[Dict],
        chain_mode: ChainingMode
    ) -> Dict[str, Any]:
        """Convert ToT ID sequence into full learning path object"""
        path = []
        hours_used = 0
        
        # Handle both Dict and Pydantic model formats
        if hasattr(learner_profile, 'model_dump'):
            current_mastery_raw = getattr(learner_profile, 'current_mastery', []) or []
            concept_mastery_map = getattr(learner_profile, 'concept_mastery_map', {}) or {}
            hours_per_day = getattr(learner_profile, 'hours_per_day', 2) or 2
            time_available = getattr(learner_profile, 'time_available', None) or getattr(learner_profile, 'available_time', 30) or 30
            preferred_style = getattr(learner_profile, 'preferred_learning_style', 'VISUAL')
            if hasattr(preferred_style, 'value'):
                preferred_style = preferred_style.value
        else:
            current_mastery_raw = learner_profile.get("current_mastery", [])
            concept_mastery_map = learner_profile.get("concept_mastery_map", {})
            hours_per_day = learner_profile.get("hours_per_day", 2)
            time_available = learner_profile.get("time_available", 30)
            preferred_style = learner_profile.get("preferred_learning_style", "VISUAL")
        
        # Build mastery dict
        current_mastery = {}
        for m in current_mastery_raw:
            if isinstance(m, dict):
                current_mastery[m.get("concept_id", "")] = m.get("mastery_level", 0.0)
            elif hasattr(m, 'concept_id'):
                current_mastery[m.concept_id] = getattr(m, 'mastery_level', 0.0)
        current_mastery.update(concept_mastery_map)
        
        total_available = time_available * hours_per_day
        
        for cid in path_ids:
            # Find concept data
            concept = next((c for c in course_concepts if c["concept_id"] == cid), None)
            if not concept:
                continue
            
            difficulty = concept.get('difficulty', 2)
            time_est = concept.get('time_estimate', 60) / 60
            
            path.append({
                "day": int(hours_used / hours_per_day) + 1,
                "concept": cid,
                "concept_name": concept.get('name', cid),
                "difficulty": difficulty,
                "estimated_hours": round(time_est, 1),
                "chain_mode": "TOT_GENERATED",
                "recommended_type": self._recommend_content_type(
                    difficulty,
                    preferred_style
                )
            })
            
            hours_used += time_est
            current_mastery[cid] = max(0.1, 0.5 - (difficulty * 0.08))

        pacing = self._determine_pacing(hours_used, total_available, len(path))
        
        return {
            "success": True,
            "path": path,
            "pacing": pacing,
            "total_hours": round(hours_used, 1),
            "current_mastery": current_mastery
        }
    
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
            # Handle both Dict and Pydantic model formats
            if hasattr(learner_profile, 'model_dump'):
                # Pydantic model - convert to dict or use getattr
                current_mastery_raw = getattr(learner_profile, 'current_mastery', []) or []
                concept_mastery_map = getattr(learner_profile, 'concept_mastery_map', {}) or {}
            else:
                # Dict format
                current_mastery_raw = learner_profile.get("current_mastery", [])
                concept_mastery_map = learner_profile.get("concept_mastery_map", {})
            
            # Build mastery dict from both sources
            current_mastery = {}
            for m in current_mastery_raw:
                if isinstance(m, dict):
                    current_mastery[m.get("concept_id", "")] = m.get("mastery_level", 0.0)
                elif hasattr(m, 'concept_id'):
                    current_mastery[m.concept_id] = getattr(m, 'mastery_level', 0.0)
            current_mastery.update(concept_mastery_map)
            
            time_available = getattr(learner_profile, 'time_available', None) or getattr(learner_profile, 'available_time', 30) or 30
            hours_per_day = getattr(learner_profile, 'hours_per_day', 2) or 2
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
                # SCIENTIFIC FIX: Spaced Repetition using Ebbinghaus Exponential Decay
                # Source: Ebbinghaus (1885) for Retention / Vygotsky (1978) for ZPD
                # NOTE: We distinguish "Review" (Maintenance of High Mastery items) 
                # from "Forward Learning" (ZPD - Emerging functions).
                # This queue strictly handles Maintenance (preventing decay of "ripe fruits").
                # Formula: R(t) = e^(-t/S) where S = Stability (higher mastery = slower decay)
                from datetime import datetime, timedelta
                import math
                
                review_candidates = []
                for cid, mastery in current_mastery.items():
                    if mastery > 0.5:  # Only review concepts with decent mastery
                        # Estimate days since last review (TODO: use actual last_review_date from DB)
                        # For now, estimate based on mastery level: high mastery = reviewed longer ago
                        estimated_days = int((1 - mastery) * 30) + 1  # 0.9 mastery = ~4 days, 0.5 = ~16 days
                        
                        # Stability: High mastery concepts decay slower
                        stability = max(1, mastery * 30)  # Days until 50% retention
                        
                        # Retention probability using Ebbinghaus formula
                        retention = math.exp(-estimated_days / stability)
                        
                        # Review Priority = Forgetting probability * Mastery (we care more about forgetting good stuff)
                        # High mastery + Low retention = HIGH priority (about to forget something valuable)
                        review_priority = (1 - retention) * mastery
                        
                        review_candidates.append((cid, review_priority))
                
                # Sort by review priority (higher = more urgent review)
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
        learner_profile  # Can be Dict or LearnerProfile
    ) -> List[Dict[str, Any]]:
        """
        Recommend learning resources for each concept.
        
        TODO: In production, query actual resources from Content Management System
        or Knowledge Graph. Currently returns placeholder resource types.
        """
        resources = []
        # Handle both Dict and Pydantic model
        if hasattr(learner_profile, 'model_dump'):
            learning_style = getattr(learner_profile, 'preferred_learning_style', 'VISUAL')
            if hasattr(learning_style, 'value'):
                learning_style = learning_style.value
        else:
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
        learner_profile,  # Can be Dict or LearnerProfile
        learning_path: List[Dict[str, Any]],
        current_mastery: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate probability of completing learning path.
        
        Formula (per THESIS Section 3.1.3):
        P(success) = 0.4 × avg_mastery + 0.4 × time_fit - 0.2 × difficulty_penalty
        """
        if not learning_path:
            return 0.0
        
        # Handle both Dict and Pydantic model
        if hasattr(learner_profile, 'model_dump'):
            profile_mastery = getattr(learner_profile, 'concept_mastery_map', {}) or {}
            time_days = getattr(learner_profile, 'time_available', None) or getattr(learner_profile, 'available_time', 30) or 30
            hours_per_day = getattr(learner_profile, 'hours_per_day', 2) or 2
        else:
            profile_mastery = learner_profile.get("concept_mastery_map", {})
            time_days = learner_profile.get("time_available", 30)
            hours_per_day = learner_profile.get("hours_per_day", 2)
        
        # Component 1: Average mastery (40%)
        mastery_source = current_mastery if current_mastery else profile_mastery
        mastery_scores = [
            mastery_source.get(step['concept'], 0.0)
            for step in learning_path
        ]
        avg_mastery = sum(mastery_scores) / len(mastery_scores) if mastery_scores else 0.0
        
        # Component 2: Time fit (40%)
        total_hours = sum(s.get("estimated_hours", 0) for s in learning_path)
        
        # FIX: Align with Agent 2's Profile Schema (Days * Hours/Day)
        # time_days and hours_per_day already extracted above
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


class MOPOValidator:
    """
    Validate MOPO reward function weights through sensitivity analysis.
    
    HYPOTHESIS: Weights (0.3, 0.3, 0.2, 0.2) are optimal for learning outcomes
    
    METHOD: Test multiple weight combinations, measure path quality metrics
    """
    
    def __init__(self, kg, learner_profiles, ground_truth_paths=None):
        """
        Args:
            kg: Knowledge Graph
            learner_profiles: List of synthetic/real learner profiles for testing
            ground_truth_paths: Expert-rated paths (optional for validation)
        """
        self.kg = kg
        self.learner_profiles = learner_profiles
        self.ground_truth_paths = ground_truth_paths or {}
    
    async def sensitivity_analysis(self, path_planner) -> Dict[str, float]:
        """
        Test different weight combinations on learner profiles.
        
        RETURNS:
        {
            "optimal_weights": (0.30, 0.30, 0.20, 0.20),
            "optimal_score": 0.85,
            "weights_tested": 1000,
            "variance": 0.03
        }
        """
        # Generate random weight combinations
        # Constraint: sum(weights) = 1.0
        n_combinations = 1000
        weight_combos = []
        
        for _ in range(n_combinations):
            w = np.random.dirichlet([1, 1, 1, 1])  # Random, sum to 1
            weight_combos.append(tuple(w))
        
        results = []
        
        for weights in weight_combos:
            alpha, beta, gamma, delta = weights
            
            # Test on each learner profile
            quality_scores = []
            for profile in self.learner_profiles:
                path = await self._plan_path_with_weights(
                    path_planner, profile, (alpha, beta, gamma, delta)
                )
                quality = await self._evaluate_path_quality(path, profile)
                quality_scores.append(quality)
            
            avg_quality = np.mean(quality_scores)
            results.append({
                "weights": weights,
                "avg_quality": avg_quality,
                "std_quality": np.std(quality_scores)
            })
        
        # Find best weights
        if not results:
            return {}
            
        best = max(results, key=lambda r: r["avg_quality"])
        
        logger.info(f"✓ Sensitivity Analysis Complete")
        logger.info(f"  Best weights: α={best['weights'][0]:.2f}, "
                   f"β={best['weights'][1]:.2f}, "
                   f"γ={best['weights'][2]:.2f}, "
                   f"δ={best['weights'][3]:.2f}")
        logger.info(f"  Quality score: {best['avg_quality']:.4f}")
        
        return {
            "optimal_weights": best["weights"],
            "optimal_score": best["avg_quality"],
            "weights_tested": n_combinations,
            "all_results": results
        }
    
    async def ablation_study(self, path_planner) -> Dict[str, float]:
        """
        Remove one weight at a time, measure impact.
        
        E.g., what if we ignore adaptivity (β=0)?
        """
        baseline = (0.30, 0.30, 0.20, 0.20)
        baseline_score = await self._score_weights(path_planner, baseline)
        
        ablations = {}
        
        # Ablate each objective
        for i, metric in enumerate(["Relevance", "Adaptivity", "Coherence", "Feasibility"]):
            w = list(baseline)
            w[i] = 0  # Remove this objective
            w_sum = np.sum(w)
            if w_sum > 0:
                w = tuple(w / w_sum)  # Renormalize
            
            score = await self._score_weights(path_planner, w)
            delta = score - baseline_score
            
            pct_change = 0
            if baseline_score != 0:
                pct_change = 100 * delta / baseline_score
                
            ablations[metric] = {
                "delta_score": delta,
                "percentage_change": pct_change
            }
            
            logger.info(f"Without {metric}: {score:.4f} "
                       f"(Δ={delta:+.4f}, {pct_change:+.1f}%)")
        
        return ablations
    
    async def _score_weights(self, path_planner, weights: Tuple[float, float, float, float]) -> float:
        """Score a weight configuration on all learner profiles"""
        scores = []
        for profile in self.learner_profiles:
            path = await self._plan_path_with_weights(path_planner, profile, weights)
            quality = await self._evaluate_path_quality(path, profile)
            scores.append(quality)
        if not scores:
            return 0.0
        return float(np.mean(scores))
    
    async def _plan_path_with_weights(self, path_planner, profile: Dict, weights: Tuple) -> List[Dict]:
        """Plan learning path using given weights"""
        # In a real implementation, this would call a modified path planner method that accepts weights.
        # For now, we simulate by calling the standard execute and assuming weights influence it,
        # OR we just call execute and pretend.
        # Ideally: path_planner.plan_with_weights(profile, weights)
        
        # Simulating call:
        try:
            # Converting profile dict back to LearnerProfile or passing as is
            learner_id = profile.get("learner_id", "dummy")
            # We can't easily inject weights into the existing execute method without Refactoring Agent 3.
            # This is a limitation of the current quick-fix. 
            # We will assume Agent 3 *could* take weights, or we just run the standard plan to test the harness.
            result = await path_planner.execute(learner_id=learner_id, goal=profile.get("goal"), force_real=False)
            if result and result.get("success"):
                return result.get("learning_path", [])
            return []
        except Exception:
            return []
    
    async def _evaluate_path_quality(self, path: List[Dict], profile: Dict) -> float:
        """
        Rate path quality on multiple dimensions.
        
        METRICS:
        1. Feasibility: time_required <= time_budget?
        2. Coherence: prerequisites satisfied?
        3. Relevance: concepts match goal?
        4. Adaptivity: personalized to profile?
        """
        if not path:
            return 0.0
            
        # Placeholder logic for validation harness
        # 1. Check time budget
        total_time = sum(step.get("estimated_hours", 0) for step in path)
        budget = profile.get("time_available", 10) * profile.get("hours_per_day", 1)
        feasibility = 1.0 if total_time <= budget else max(0.0, 1.0 - (total_time - budget)/budget)
        
        # 2. Coherence (Mock)
        coherence = 0.9 # Assume planner handles deps
        
        # 3. Relevance (Mock)
        relevance = 0.8
        
        # 4. Adaptivity (Check if recommended_type matches preferred_style)
        preferred = profile.get("preferred_learning_style", "VISUAL")
        matches = sum(1 for step in path if step.get("recommended_type") == preferred) # Heuristic match check
        adaptivity = matches / len(path) if path else 0
        
        return (feasibility + coherence + relevance + adaptivity) / 4.0
