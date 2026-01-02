import logging
import uuid
import re
import time  # FIX Issue 6: Move to top of file
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum
import json

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.semantic_scorer import SemanticScorer
from backend.core.error_classifier import ErrorClassifier
from backend.core.mastery_tracker import MasteryTracker
from backend.core.decision_engine import DecisionEngine
from backend.models.evaluation import (
    ErrorType, PathDecision, Misconception, EvaluationResult
)
from backend.config import get_settings
from backend.core.constants import (
    EVAL_MASTERY_WEIGHT,
    EVAL_DIFFICULTY_ADJUSTMENT,
    EVAL_MASTERY_BOOST,
    THRESHOLD_MASTERED,
    THRESHOLD_PROCEED,
    THRESHOLD_ALTERNATE,
    THRESHOLD_ALERT
)
from llama_index.llms.gemini import Gemini
from backend.services.instructor_notification import InstructorNotificationService

logger = logging.getLogger(__name__)

# ErrorType and PathDecision imported from backend.models.evaluation

class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent - Assess learner understanding and provide feedback.
    
    Responsibility:
    - Score learner responses (0-1)
    - Classify error types (CORRECT, CARELESS, INCOMPLETE, PROCEDURAL, CONCEPTUAL)
    - Detect misconceptions
    - Generate personalized feedback (address THEIR specific error)
    - Make path decisions (PROCEED/REMEDIATE/ALTERNATE/MASTERED)
    - Update learner progress in database
    
    Process Flow:
    1. Receive learner response + concept + expected answer
    2. Score response using LLM (0-1 scale)
    3. Classify error type (if incorrect)
    4. Detect misconceptions (what's wrong with their thinking?)
    5. Generate personalized feedback (not generic "wrong")
    6. Make path decision (what's next?)
    7. Update learner mastery in database
    8. Emit event to Path Planner (may need to adjust path)
    
    Example:
        Learner response: "WHERE combines two tables"
        Expected: "WHERE filters rows"
            ↓
        Score: 0.2 (very wrong)
        Error type: CONCEPTUAL (fundamental misunderstanding)
        Misconception: "Confuses WHERE with JOIN"
        Feedback: "I see the confusion - WHERE filters, JOIN combines.
                   Let me clarify the difference..."
        Decision: REMEDIATE (review JOIN concept first)
            ↓
        Update: Set WHERE mastery to 0.2, flag for remediation
    """
    
    # FIX Issue 8: Define pattern at class level (compiled once)
    ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    # Path decision adjustment constants (Now from constants.py)
    DIFFICULTY_ADJUSTMENT = EVAL_DIFFICULTY_ADJUSTMENT
    MASTERY_BOOST = EVAL_MASTERY_BOOST
    
    # FIX Issue 5: Mastery update weight constant (Legacy, kept for compatibility)
    MASTERY_WEIGHT = EVAL_MASTERY_WEIGHT
    
    # SCIENTIFIC FIX: Bayesian Knowledge Tracing (BKT) Parameters
    # Source: Corbett & Anderson (1994)
    P_LEARN = 0.1      # Probability of learning after one attempt
    P_GUESS = 0.25     # Probability of guessing correctly without knowing
    P_SLIP = 0.10      # Probability of making a mistake despite knowing
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None,
                 embedding_model=None, course_kg=None, personal_kg=None):
        """
        Initialize Evaluator Agent.
        
        Args:
            agent_id: Unique agent identifier
            state_manager: Central state manager
            event_bus: Event bus for inter-agent communication
            llm: LLM instance (Gemini by default)
            embedding_model: Sentence transformer for semantic similarity
            course_kg: Course Knowledge Graph accessor
            personal_kg: Personal Knowledge Graph accessor
        """
        super().__init__(agent_id, AgentType.EVALUATOR, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or Gemini(
            model=self.settings.GEMINI_MODEL,
            api_key=self.settings.GOOGLE_API_KEY
        )
        self.logger = logging.getLogger(f"EvaluatorAgent.{agent_id}")
        
        # Store KG references
        self.course_kg = course_kg
        self.personal_kg = personal_kg
        
        # Initialize core modules
        self.scorer = SemanticScorer(
            llm_client=self.llm,
            embedding_model=embedding_model,
            course_kg=course_kg
        )
        self.classifier = ErrorClassifier(
            course_kg=course_kg,
            embedding_model=embedding_model
        )
        self.tracker = MasteryTracker(
            personal_kg=personal_kg,
            course_kg=course_kg
        )
        
        # FIX Issue 3+4: Add concept cache with TTL tracking
        self._concept_cache = {}  # {concept_id: {"data": concept, "timestamp": time}}
        self._cache_ttl = 3600  # 1 hour TTL
        
        # Initialize Notification Service
        self.notification_service = InstructorNotificationService()
        
        # Event subscriptions
        
        # Event subscriptions
        if event_bus and hasattr(event_bus, 'subscribe'):
            event_bus.subscribe('TUTOR_ASSESSMENT_READY', self._on_assessment_ready)
            self.logger.info("Subscribed to TUTOR_ASSESSMENT_READY")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method - evaluate learner response.
        
        Args:
            learner_id: str - Learner ID
            concept_id: str - Concept being evaluated
            learner_response: str - Learner's answer
            expected_answer: str - What they should answer
            correct_answer_explanation: str - Why it's right
            
        Returns:
            Dict with evaluation results
        """
        try:
            # FIX Issue 4: Strip all IDs for consistency
            learner_id = (kwargs.get("learner_id") or "").strip()
            concept_id = (kwargs.get("concept_id") or "").strip()
            learner_response = (kwargs.get("learner_response") or "").strip()
            expected_answer = (kwargs.get("expected_answer") or "").strip()
            correct_answer_explanation = kwargs.get("correct_answer_explanation", "")
            
            # Validate required inputs
            if not all([learner_id, concept_id, learner_response]):
                return {
                    "success": False,
                    "error": "learner_id, concept_id, learner_response required",
                    "agent_id": self.agent_id
                }
            
            # Validate ID format (alphanumeric, underscore, hyphen only)
            if not self.ID_PATTERN.match(learner_id):
                return {
                    "success": False,
                    "error": f"Invalid learner_id format: {learner_id}",
                    "agent_id": self.agent_id
                }
            if not self.ID_PATTERN.match(concept_id):
                return {
                    "success": False,
                    "error": f"Invalid concept_id format: {concept_id}",
                    "agent_id": self.agent_id
                }
            
            # Warn if expected_answer missing (impacts scoring accuracy)
            if not expected_answer:
                self.logger.warning(f"No expected_answer provided for {concept_id} - scoring may be less accurate")
            
            self.logger.info(f"📊 Evaluating {learner_id} on {concept_id}")
            
            # Step 1: Get concept details (with cache + TTL)
            cache_entry = self._concept_cache.get(concept_id)
            
            # FIX Issue 4: Check TTL
            if cache_entry and (time.time() - cache_entry["timestamp"] < self._cache_ttl):
                # FIX Issue 5: Return copy to prevent mutation
                concept = cache_entry["data"].copy()
                self.logger.debug(f"Concept {concept_id} loaded from cache")
            else:
                neo4j = self.state_manager.neo4j
                # Expanded query to get all concept properties
                concept_result = await neo4j.run_query(
                    """
                    MATCH (c:CourseConcept {concept_id: $concept_id})
                    OPTIONAL MATCH (c)-[:HAS_PREREQUISITE]->(prereq:CourseConcept)
                    RETURN c,
                           c.common_misconceptions as misconceptions,
                           collect(DISTINCT prereq.concept_id) as prerequisites
                    """,
                    concept_id=concept_id
                )
                
                if not concept_result:
                    return {
                        "success": False,
                        "error": f"Concept not found: {concept_id}",
                        "agent_id": self.agent_id
                    }
                
                concept = concept_result[0].get("c", {})
                # FIX Issue 7: Only add if not already present
                if "common_misconceptions" not in concept:
                    concept["common_misconceptions"] = concept_result[0].get("misconceptions", [])
                if "prerequisites" not in concept:
                    concept["prerequisites"] = concept_result[0].get("prerequisites", [])
                
                self.logger.debug(f"Concept {concept_id} loaded: {concept.get('name', 'Unknown')}")
                
                # FIX Issue 4: Cache with timestamp for TTL
                self._concept_cache[concept_id] = {
                    "data": concept.copy(),  # FIX Issue 5: Store copy
                    "timestamp": time.time()
                }
            
            # Step 2: Score response
            score_result = await self._score_response(
                learner_response=learner_response,
                expected_answer=expected_answer,
                explanation=correct_answer_explanation
            )
            
            score = score_result["score"]  # 0-1
            
            # Step 3-5: If incorrect, classify error + detect misconception + feedback
            error_type = ErrorType.CORRECT
            misconception = None
            feedback = None
            
            if score < 0.8:
                # Step 3: Classify error (with concept context)
                error_result = await self._classify_error(
                    learner_response=learner_response,
                    expected_answer=expected_answer,
                    concept=concept  # FIX Issue 1: Add concept context
                )
                error_type = ErrorType(error_result["error_type"])
                
                # Step 4: Detect misconception
                misconception_result = await self._detect_misconception(
                    learner_response=learner_response,
                    concept=concept,
                    error_type=error_type
                )
                misconception = misconception_result.get("misconception")
                
                # Step 5: Generate feedback
                feedback_result = await self._generate_feedback(
                    learner_response=learner_response,
                    expected_answer=expected_answer,
                    error_type=error_type,
                    misconception=misconception,
                    explanation=correct_answer_explanation
                )
                feedback = feedback_result["feedback"]
            else:
                # Correct answer - generate praise
                feedback = f"Excellent! Your answer '{learner_response}' is correct. "
                feedback += f"You understand that {expected_answer}. Well done!"
            
            # Step 6: Make path decision
            learner_profile = await self.state_manager.get_learner_profile(learner_id)
            current_mastery = 0.0
            if learner_profile:
                for mastery in learner_profile.get("current_mastery", []):
                    if mastery.get("concept_id") == concept_id:
                        current_mastery = mastery.get("mastery_level", 0.0)
                        break
            
            decision = await self._make_path_decision(
                score=score,
                current_mastery=current_mastery,
                error_type=error_type,
                concept_difficulty=concept.get("difficulty", 2)
            )
            
            # Step 7: Update learner progress
            new_mastery = await self._update_learner_mastery(
                learner_id=learner_id,
                concept_id=concept_id,
                score=score,
                current_mastery=current_mastery
            )
            
            # Prepare result
            result = {
                "success": True,
                "agent_id": self.agent_id,
                "learner_id": learner_id,
                "concept_id": concept_id,
                "score": score,
                "error_type": error_type.value,
                "misconception": misconception,
                "feedback": feedback,
                "decision": decision.value,
                "new_mastery": new_mastery,
                "timestamp": datetime.now().isoformat()
            }
            
            # Step 8: Emit events
            event_payload = {
                "learner_id": learner_id,
                "concept_id": concept_id,
                "score": score,
                "decision": decision.value,
                "new_mastery": new_mastery
            }
            
            # FIX: Debug log for event payload
            self.logger.debug(f"Emitting EVALUATION_COMPLETED: {event_payload}")
            
            # FIX Issue 9-10: Use EVALUATION_COMPLETED to match subscriber events
            await self.send_message(
                receiver="path_planner",
                message_type="EVALUATION_COMPLETED",
                payload=event_payload
            )
            
            if score < THRESHOLD_ALERT:
                # FIX Issue 1: Fetch actual attempts from learner profile
                attempts = 1
                if learner_profile:
                    concept_history = learner_profile.get("concept_attempts", {})
                    attempts = concept_history.get(concept_id, {}).get("attempts", 1)
                
                # Trigger Instructor Alert for Critical Failure
                await self.notification_service.notify_failure(
                    learner_id=learner_id,
                    concept_id=concept_id,
                    score=score,
                    attempts=attempts
                )

            self.logger.info(f"✅ Evaluation complete: {error_type.value} ({score:.1%})")
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ Evaluation failed: {e}")
            
            # FIX Issue 3: Emit error event so path_planner knows evaluation failed
            try:
                await self.send_message(
                    receiver="path_planner",
                    message_type="EVALUATION_FAILED",
                    payload={
                        "learner_id": kwargs.get("learner_id"),
                        "concept_id": kwargs.get("concept_id"),
                        "error": str(e)
                    }
                )
            except Exception:
                pass  # Best effort - don't fail silently
            
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    async def _score_response(
        self,
        learner_response: str,
        expected_answer: str,
        explanation: str,
        target_bloom_level: int = 2  # Default: UNDERSTAND
    ) -> Dict[str, Any]:
        """
        Score learner response with Bloom's Taxonomy awareness.
        
        Scientific Basis: Bloom (1956) - Taxonomy of Educational Objectives
        
        Bloom Levels:
        1 = Remember (Recall facts)
        2 = Understand (Explain concepts)
        3 = Apply (Use in new situations)
        4 = Analyze (Break down, compare)
        5 = Evaluate (Justify, critique)
        6 = Create (Design, construct)
        
        Scoring Rule: If target is "Apply" (3+), but answer is just "Recall", max score = 0.6.
        """
        try:
            bloom_level_names = {
                1: "Remember (recall facts)",
                2: "Understand (explain meaning)",
                3: "Apply (use in new situations)",
                4: "Analyze (compare, contrast, break down)",
                5: "Evaluate (judge, justify)",
                6: "Create (design, build)"
            }
            target_bloom_name = bloom_level_names.get(target_bloom_level, "Understand")
            
            prompt = f"""
            Score this learner response with BLOOM'S TAXONOMY awareness.
            
            TARGET COGNITIVE LEVEL: {target_bloom_level} - {target_bloom_name}
            
            Learner response: {learner_response}
            Expected answer: {expected_answer}
            Correct explanation: {explanation}
            
            SCORING RULES:
            - If Target Bloom = 1-2 (Remember/Understand): Score primarily on ACCURACY.
            - If Target Bloom = 3+ (Apply/Analyze/Evaluate/Create): Score on REASONING quality.
            - If learner provides CORRECT DEFINITION but fails to APPLY it: max score = 0.6.
            - If learner demonstrates higher-level thinking: bonus up to 1.0.
            
            Return ONLY valid JSON:
            {{"score": 0.0-1.0, "bloom_achieved": 1-6, "reasoning": "..."}}
            
            Example: {{"score": 0.7, "bloom_achieved": 2, "reasoning": "Correct definition but no application shown"}}
            """
            
            response = await self.llm.acomplete(prompt)
            score_text = response.text
            
            # FIX Issue 6: Log if LLM response is empty
            if not score_text or not score_text.strip():
                self.logger.warning(f"Empty LLM response for Bloom scoring - using fallback")
            
            # Parse JSON response
            try:
                # Try to extract score from JSON
                score_match = re.search(r'"score"\s*:\s*([\d.]+)', score_text or "")
                bloom_match = re.search(r'"bloom_achieved"\s*:\s*(\d+)', score_text or "")
                
                if score_match:
                    score = float(score_match.group(1))
                    bloom_achieved = int(bloom_match.group(1)) if bloom_match else target_bloom_level
                    
                    # Apply Bloom's penalty: If high target but low achievement, cap score
                    if target_bloom_level >= 3 and bloom_achieved <= 2:
                        original_score = score
                        score = min(0.6, score)
                        self.logger.debug(
                            f"Bloom penalty applied: target={target_bloom_level}, achieved={bloom_achieved}, "
                            f"score={original_score:.2f} -> {score:.2f}"
                        )
                else:
                    # Fallback: word overlap
                    learner_words = set(learner_response.lower().split())
                    expected_words = set(expected_answer.lower().split())
                    if expected_words:
                        overlap = len(learner_words & expected_words) / len(expected_words)
                        score = min(0.8, overlap)
                    else:
                        self.logger.warning(f"Cannot score - expected_answer is empty")
                        score = 0.0
                        
                score = max(0.0, min(1.0, score))  # Clamp to 0-1
            except Exception as parse_error:
                self.logger.warning(f"Bloom score parsing error ({type(parse_error).__name__}): {parse_error}")
                score = 0.0 if learner_response.lower() != expected_answer.lower() else 1.0
            
            return {"success": True, "score": score}
        
        except Exception as e:
            self.logger.error(f"Bloom scoring error: {e}")
            return {"success": False, "score": 0.0}
    
    async def _classify_error(
        self,
        learner_response: str,
        expected_answer: str,
        concept: Dict[str, Any] = None  # FIX Issue 1: Add concept parameter
    ) -> Dict[str, Any]:
        """Classify error type with concept context"""
        try:
            # FIX Issue 1: Include concept name for context
            concept_name = concept.get("name", "Unknown") if concept else "Unknown"
            
            prompt = f"""
            Classify this error for the concept "{concept_name}":
            
            Learner response: {learner_response}
            Expected: {expected_answer}
            
            Classification options:
            - CARELESS: Simple typo or arithmetic mistake
            - INCOMPLETE: Partially correct, missing parts
            - PROCEDURAL: Wrong approach or steps
            - CONCEPTUAL: Fundamental misunderstanding
            
            Return ONLY the classification name.
            Example: CONCEPTUAL
            """
            
            response = await self.llm.acomplete(prompt)
            error_type = response.text.strip().upper()
            
            # Validate
            valid_types = ["CARELESS", "INCOMPLETE", "PROCEDURAL", "CONCEPTUAL"]
            if error_type not in valid_types:
                # FIX Issue 4: Default to CARELESS (less pessimistic)
                self.logger.warning(f"Invalid error_type '{error_type}' - defaulting to CARELESS")
                error_type = "CARELESS"
            
            return {"success": True, "error_type": error_type}
        
        except Exception as e:
            self.logger.error(f"Error classification error: {e}")
            return {"success": False, "error_type": "CARELESS"}  # FIX Issue 4: Changed from CONCEPTUAL
    
    async def _detect_misconception(
        self,
        learner_response: str,
        concept: Dict[str, Any],
        error_type: ErrorType
    ) -> Dict[str, Any]:
        """Detect learner's misconception with reference to known misconceptions"""
        try:
            if error_type == ErrorType.CORRECT:
                return {"success": True, "misconception": None}
            
            concept_name = concept.get("name", "Unknown")
            # FIX Issue 2: Get known misconceptions from concept
            known_misconceptions = concept.get("common_misconceptions", [])
            misconceptions_str = ", ".join(known_misconceptions) if known_misconceptions else "None known"
            
            prompt = f"""
            What misconception does this learner have?
            
            Concept: {concept_name}
            Learner response: {learner_response}
            Known common misconceptions for this concept: {misconceptions_str}
            
            Identify the mistaken belief or mental model.
            If the error matches a known misconception, reference it.
            Return ONLY a short sentence describing the misconception.
            
            Example: "Thinks WHERE joins tables (confuses with JOIN)"
            """
            
            response = await self.llm.acomplete(prompt)
            misconception = response.text.strip()
            
            return {"success": True, "misconception": misconception}
        
        except Exception as e:
            self.logger.error(f"Misconception detection error: {e}")
            return {"success": False, "misconception": None}
    
    async def _generate_feedback(
        self,
        learner_response: str,
        expected_answer: str,
        error_type: ErrorType,
        misconception: Optional[str],
        explanation: str
    ) -> Dict[str, Any]:
        """Generate personalized feedback"""
        try:
            prompt = f"""
            Generate personalized feedback addressing THEIR specific error.
            NOT generic "that's wrong" - address THEIR misconception.
            
            Learner response: {learner_response}
            Expected: {expected_answer}
            Error type: {error_type.value}
            Misconception: {misconception}
            Correct explanation: {explanation}
            
            Return personalized, encouraging feedback (2-3 sentences).
            Address the misconception, not just the wrong answer.
            
            Example: "I see where the confusion comes from - you're thinking
            WHERE joins tables, which is actually what JOIN does. Let me
            clarify the difference..."
            """
            
            response = await self.llm.acomplete(prompt)
            feedback = response.text.strip() if response.text else ""
            
            # FIX Issue 5: Check empty LLM response
            if not feedback:
                self.logger.warning("Empty LLM feedback - using fallback")
                feedback = self._get_fallback_feedback(error_type, misconception)
            
            return {"success": True, "feedback": feedback}
        
        except Exception as e:
            self.logger.error(f"Feedback generation error: {e}")
            # FIX Issue 6: Personalized fallback based on error type
            fallback = self._get_fallback_feedback(error_type, misconception)
            return {"success": False, "feedback": fallback}
    
    def _get_fallback_feedback(self, error_type: ErrorType, misconception: Optional[str]) -> str:
        """Generate personalized fallback feedback based on error type"""
        base_messages = {
            ErrorType.CARELESS: "I noticed a small slip-up. Let's look at this more carefully.",
            ErrorType.INCOMPLETE: "You're on the right track, but let's add more detail.",
            ErrorType.PROCEDURAL: "The concept is clear, but let's review the correct steps.",
            ErrorType.CONCEPTUAL: "Let's take a step back and clarify this concept together.",
        }
        
        feedback = base_messages.get(error_type, "Let's review this concept together.")
        
        if misconception:
            feedback += f" It seems like {misconception}."
        
        return feedback
    
    async def _make_path_decision(
        self,
        score: float,
        current_mastery: float,
        error_type: ErrorType,
        concept_difficulty: int
    ) -> PathDecision:
        """
        Make decision for next learning action (per Thesis Table 3.10).
        
        Decision Logic with adjustments:
        - FIX Issue 1: Use current_mastery to adjust MASTERED threshold
        - FIX Issue 2: Use concept_difficulty for lenient thresholds on hard concepts
        
        Base Thresholds:
        - score >= 0.9 -> MASTERED
        - score >= 0.8 -> PROCEED
        - score >= 0.6 -> ALTERNATE
        - score < 0.6 + CONCEPTUAL -> REMEDIATE
        - score < 0.6 + Other -> RETRY
        """
        
        # Adjust thresholds based on concept difficulty (1-5 scale)
        # Harder concepts (4-5) get slightly lower thresholds
        difficulty_adjustment = 0.0
        if concept_difficulty >= 4:
            difficulty_adjustment = self.DIFFICULTY_ADJUSTMENT
        
        # Adjust MASTERED threshold based on current mastery
        # If learner already has high mastery, be slightly more lenient
        mastery_boost = 0.0
        if current_mastery >= 0.7:
            mastery_boost = self.MASTERY_BOOST
        
        # Adjusted thresholds
        mastered_threshold = THRESHOLD_MASTERED - difficulty_adjustment - mastery_boost
        proceed_threshold = THRESHOLD_PROCEED - difficulty_adjustment
        alternate_threshold = THRESHOLD_ALTERNATE - difficulty_adjustment
        
        # Determine decision
        if score >= mastered_threshold:
            decision = PathDecision.MASTERED
        elif score >= proceed_threshold:
            decision = PathDecision.PROCEED
        elif score >= alternate_threshold:
            decision = PathDecision.ALTERNATE
        else:
            # Low score - check error type
            if error_type == ErrorType.CONCEPTUAL:
                decision = PathDecision.REMEDIATE
            else:
                decision = PathDecision.RETRY
        
        # FIX Issue 4: Log decision and adjusted thresholds
        self.logger.debug(
            f"Path decision: {decision.value} | "
            f"score={score:.2f}, thresholds=[M:{mastered_threshold:.2f}, P:{proceed_threshold:.2f}, A:{alternate_threshold:.2f}] | "
            f"adjustments=[difficulty:{difficulty_adjustment:.2f}, mastery_boost:{mastery_boost:.2f}]"
        )
        
        return decision
    
    async def _update_learner_mastery(
        self,
        learner_id: str,
        concept_id: str,
        score: float,
        current_mastery: float
    ) -> float:
        """
        Update learner's mastery level using Bayesian Knowledge Tracing (BKT).
        
        Scientific Basis: Corbett & Anderson (1994)
        
        BKT models knowledge as a hidden state. The update uses:
        - P(Know|Correct) = P(Correct|Know) * P(Know) / P(Correct)
        - P(Know|Incorrect) = P(Incorrect|Know) * P(Know) / P(Incorrect)
        - Then applies learning gain: P(Know) += (1 - P(Know)) * P_LEARN
        """
        try:
            prior_mastery = current_mastery
            is_correct = score >= 0.8  # Threshold for "correct"
            
            # Bayesian Update
            if is_correct:
                # P(Correct|Know) = 1 - P_SLIP; P(Correct|NotKnow) = P_GUESS
                p_correct = (1 - self.P_SLIP) * prior_mastery + self.P_GUESS * (1 - prior_mastery)
                if p_correct > 0:
                    posterior = ((1 - self.P_SLIP) * prior_mastery) / p_correct
                else:
                    posterior = prior_mastery
            else:
                # P(Incorrect|Know) = P_SLIP; P(Incorrect|NotKnow) = 1 - P_GUESS
                p_incorrect = self.P_SLIP * prior_mastery + (1 - self.P_GUESS) * (1 - prior_mastery)
                if p_incorrect > 0:
                    posterior = (self.P_SLIP * prior_mastery) / p_incorrect
                else:
                    posterior = prior_mastery
            
            # Apply learning gain (even after incorrect, some learning occurs)
            new_mastery = posterior + (1 - posterior) * self.P_LEARN
            new_mastery = max(0.0, min(1.0, new_mastery))  # Clamp to [0, 1]
            
            # Debug log for BKT update
            self.logger.debug(
                f"BKT update: {learner_id}/{concept_id} | "
                f"prior={prior_mastery:.2f}, correct={is_correct} -> posterior={new_mastery:.2f}"
            )
            
            # Save to database
            await self.save_state(
                f"learner_mastery:{learner_id}:{concept_id}",
                {"mastery": new_mastery, "updated": datetime.now().isoformat()}
            )
            
            return new_mastery
        
        except Exception as e:
            self.logger.error(f"BKT mastery update error: {e}")
            return current_mastery
    
    # ==========================================
    # EVENT HANDLERS (Per THESIS Integration)
    # ==========================================
    
    async def _on_assessment_ready(self, event: Dict):
        """
        Handle TUTOR_ASSESSMENT_READY event from Tutor Agent.
        
        Event payload:
        {
            'learner_id': str,
            'concept_id': str,
            'learner_answer': str (optional),
            'expected_answer': str (optional),
            'dialogue_transcript': list
        }
        """
        try:
            learner_id = event.get('learner_id')
            concept_id = event.get('concept_id')
            
            if not learner_id or not concept_id:
                self.logger.warning("Missing learner_id or concept_id in event")
                return
            
            self.logger.info(f"TUTOR_ASSESSMENT_READY: Evaluating {learner_id}/{concept_id}")
            
            # Execute evaluation
            # Support both 'learner_answer' and 'learner_response' for compatibility
            learner_response = (event.get('learner_response') or event.get('learner_answer') or '').strip()
            
            # FIX Issue 6: Check empty response with clear warning
            if not learner_response:
                self.logger.warning(f"No learner_response in event for {learner_id}/{concept_id} - skipping evaluation")
                return
            
            result = await self.execute(
                learner_id=learner_id,
                concept_id=concept_id,
                learner_response=learner_response,
                expected_answer=event.get('expected_answer', ''),
                dialogue_transcript=event.get('dialogue_transcript', [])
            )
            
            if result.get('success'):
                self.logger.info(
                    f"Evaluation complete: score={result.get('score', 0):.2f}, "
                    f"decision={result.get('evaluation', {}).get('path_decision', 'UNKNOWN')}"
                )
        except Exception as e:
            self.logger.exception(f"Error handling TUTOR_ASSESSMENT_READY: {e}")
    
    async def generate_feedback_for_kag(
        self, 
        learner_id: str, 
        concept_id: str,
        misconceptions: List[Misconception],
        error_type: ErrorType
    ) -> Dict:
        """Generate diagnostic feedback for KAG artifact generation"""
        return {
            'learner_id': learner_id,
            'concept_id': concept_id,
            'source': 'evaluation',
            'misconceptions': [m.to_dict() for m in misconceptions],
            'struggle_area': error_type.value,
            'needs_remediation': len(misconceptions) > 0 or error_type == ErrorType.CONCEPTUAL
        }

