from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.rl_engine import RLEngine, BanditStrategy
from backend.core.constants import (
    CHAIN_RELATIONSHIPS,
    MASTERY_PREREQUISITE_THRESHOLD,
    CONCEPT_BASE_TIME,
    DIFFICULTY_MULTIPLIER,
    TIME_BUDGET_FACTOR,
    MAX_PATH_CONCEPTS,
    PACING_AGGRESSIVE_THRESHOLD,
    PACING_MODERATE_THRESHOLD,
    SUCCESS_PROB_MASTERY_WEIGHT,
    SUCCESS_PROB_TIME_WEIGHT,
    SUCCESS_PROB_DIFFICULTY_WEIGHT
)
from backend.models import LearnerProfile
from backend.config import get_settings

logger = logging.getLogger(__name__)


class ChainingMode(str, Enum):
    """Adaptive Sequencing Modes per THESIS Section 3.1.2"""
    FORWARD = "FORWARD"    # Success -> NEXT, IS_PREREQUISITE_OF
    BACKWARD = "BACKWARD"  # Remediate -> REQUIRES (go to prerequisites)
    LATERAL = "LATERAL"    # Stuck -> SIMILAR_TO, HAS_ALTERNATIVE_PATH, REMEDIATES


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
        self.rl_engine = RLEngine(strategy=BanditStrategy.UCB)
        self.logger = logging.getLogger(f"PathPlannerAgent.{agent_id}")
        
        # Relationship type priorities for each chaining mode
        self.CHAIN_RELATIONSHIPS = {
            ChainingMode.FORWARD: ["NEXT", "IS_PREREQUISITE_OF"],
            ChainingMode.BACKWARD: ["REQUIRES"],
            ChainingMode.LATERAL: ["SIMILAR_TO", "HAS_ALTERNATIVE_PATH", "REMEDIATES"]
        }
    
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
            
            # Step 2: Get Course KG (concepts + ALL relationship types)
            neo4j = self.state_manager.neo4j
            course_concepts = await neo4j.run_query(
                """
                MATCH (c:CourseConcept) 
                RETURN c.concept_id as concept_id, 
                       c.name as name, 
                       c.difficulty as difficulty,
                       c.time_estimate as time_estimate
                """
            )
            
            # Get ALL relationship types
            course_relationships = await neo4j.run_query(
                """
                MATCH (a:CourseConcept)-[r]->(b:CourseConcept)
                RETURN a.concept_id as source, 
                       b.concept_id as target,
                       type(r) as rel_type
                """
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
            
            # Step 8: Calculate success probability
            success_prob = await self._calculate_success_probability(
                learner_profile,
                learning_path["path"]
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
        
        - PROCEED/MASTERED -> Forward chaining
        - REMEDIATE -> Backward chaining (prerequisites)
        - ALTERNATE/None -> Lateral chaining
        """
        if last_result in ["PROCEED", "MASTERED"]:
            return ChainingMode.FORWARD
        elif last_result == "REMEDIATE":
            return ChainingMode.BACKWARD
        else:  # ALTERNATE, RETRY, or None
            return ChainingMode.LATERAL
    
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
                    prerequisites=prerequisites
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
                            prerequisites=prerequisites
                        )
                    
                    if not candidates:
                        break
                
                # Use RL to select from candidates
                next_concept = self.rl_engine.select_concept(
                    learner_mastery=current_mastery,
                    prerequisites=prerequisites,
                    time_available=int(total_hours - hours_used),
                    learning_style=learner_profile.get("preferred_learning_style", "VISUAL"),
                    candidate_concepts=candidates
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
                current_mastery[next_concept] = 0.3
                day = int(hours_used / hours_per_day) + 1
            
            # Determine pacing
            pacing = self._determine_pacing(hours_used, total_hours, len(path))
            
            return {
                "success": True,
                "path": path,
                "pacing": pacing,
                "total_hours": round(hours_used, 1)
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
        prerequisites: Dict[str, List[str]]
    ) -> List[str]:
        """Get candidate concepts based on chaining mode relationships"""
        candidates = []
        
        if current_concept:
            # Get related concepts via relevant relationship types
            for rel_type in relevant_rel_types:
                if rel_type in relationship_map:
                    related = relationship_map[rel_type].get(current_concept, [])
                    candidates.extend(related)
        else:
            # No current concept - get all concepts
            candidates = [c["concept_id"] for c in course_concepts]
        
        # Filter: not visited, prerequisites met
        valid_candidates = []
        for candidate in candidates:
            if candidate in visited:
                continue
            
            # Check prerequisites
            prereqs = prerequisites.get(candidate, [])
            prereqs_met = all(
                current_mastery.get(p, 0) >= 0.5 or p in visited
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
        """Recommend learning resources for each concept"""
        resources = []
        learning_style = learner_profile.get("preferred_learning_style", "VISUAL")
        
        for step in learning_path:
            concept = step["concept"]
            
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
        Calculate probability of completing learning path.
        
        Formula (per THESIS Section 3.1.3):
        P(success) = 0.4 × avg_mastery + 0.4 × time_fit - 0.2 × difficulty_penalty
        """
        if not learning_path:
            return 0.0
        
        # Component 1: Average mastery (40%)
        concept_mastery_map = learner_profile.get("concept_mastery_map", {})
        mastery_scores = [
            concept_mastery_map.get(step['concept'], 0.0)
            for step in learning_path
        ]
        avg_mastery = sum(mastery_scores) / len(mastery_scores) if mastery_scores else 0.0
        
        # Component 2: Time fit (40%)
        total_hours = sum(s.get("estimated_hours", 0) for s in learning_path)
        available_hours = learner_profile.get("available_time", 600) / 60  # minutes -> hours
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
