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
from backend.core.llm_factory import LLMFactory
from backend.services.instructor_notification import InstructorNotificationService

logger = logging.getLogger(__name__)

# ErrorType and PathDecision imported from backend.models.evaluation

class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent - Assess learner understanding and provide feedback.
    ...
    """
    
    # FIX Issue 8: Define pattern at class level (compiled once)
    ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    # Path decision adjustment constants (Now from constants.py)
    DIFFICULTY_ADJUSTMENT = EVAL_DIFFICULTY_ADJUSTMENT
    MASTERY_BOOST = EVAL_MASTERY_BOOST
    
    # FIX Issue 5: Mastery update weight constant (Legacy, kept for compatibility)
    MASTERY_WEIGHT = EVAL_MASTERY_WEIGHT
    
    # SCIENTIFIC FIX: Hybrid DKT-LLM Parameters
    # Source: Piech et al. (2015) & Liu et al. (2024)
    P_LEARN = 0.1      # BKT: Probability of learning after one attempt
    P_GUESS = 0.25     # BKT: Probability of guessing correctly without knowing
    P_SLIP = 0.10      # BKT: Probability of making a mistake despite knowing
    
    # Hybrid Anchoring Constants
    DKT_PRIOR_WEIGHT = 0.15   # Impact of concept difficulty on prior (Difficulty 1-5 * 0.15)
    DKT_STEP_SIZE = 0.1       # Fallback step size if LLM formatting fails
    
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
        self.llm = llm or LLMFactory.get_llm()
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
            force_real: bool - Override mock settings
            
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
            force_real = kwargs.get("force_real", False)
            
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
                explanation=correct_answer_explanation,
                force_real=force_real
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
                    concept=concept,  # FIX Issue 1: Add concept context
                    force_real=force_real
                )
                error_type = ErrorType(error_result["error_type"])
                
                # Step 4: Detect misconception
                misconception_result = await self._detect_misconception(
                    learner_response=learner_response,
                    concept=concept,
                    error_type=error_type,
                    force_real=force_real
                )
                misconception = misconception_result.get("misconception")
                
                # Step 5: Generate feedback
                feedback_result = await self._generate_feedback(
                    learner_response=learner_response,
                    expected_answer=expected_answer,
                    error_type=error_type,
                    misconception=misconception,
                    explanation=correct_answer_explanation,
                    force_real=force_real
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
            
            # Step 7: Update learner progress (Hybrid DKT-LLM)
            new_mastery = await self._update_learner_mastery(
                learner_id=learner_id,
                concept_id=concept_id,
                score=score,
                current_mastery=current_mastery,
                concept_difficulty=concept.get("difficulty", 2),
                error_type=error_type,
                misconception=misconception,
                learner_response=learner_response,
                expected_answer=expected_answer,
                concept_name=concept.get("name", concept_id)
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
        target_bloom_level: int = 2,
        force_real: bool = False
    ) -> Dict[str, Any]:
        """
        Score learner response using JudgeLM Methodology (Zhu et al., 2023).
        
        Technique: Reference-as-Prior (Assistant 1 = Golden).
        Scientific Basis: "JudgeLM: Fine-tuned Large Language Models are Scalable Judges"
        """
        if self.settings.MOCK_LLM and not force_real:
             return {"success": True, "score": 0.9}

        try:
            # Construct strict JudgeLM Prompt (Figure 5 adapted)
            prompt = f"""
You are a helpful and precise assistant for checking the quality of the answer.

[Question]
The user asked a question requiring a Bloom Level {target_bloom_level} response.
(Implied Question from Truth): "{explanation}"

[The Start of Assistant 1's Answer]
{expected_answer}
[The End of Assistant 1's Answer]

[The Start of Assistant 2's Answer]
{learner_response}
[The End of Assistant 2's Answer]

[System]
We would like to request your feedback on the performance of two AI assistants in response to the user question.
Assistant 1 is the Reference Answer and receives a score of 10.
Please rate the helpfulness, relevance, accuracy, and level of details of Assistant 2's response compared to Assistant 1.
Assistant 2 receives an overall score on a scale of 1 to 10, where a higher score indicates better overall performance.

[Rubric]
- Correctness (Weight 0.6): Factual alignment with Reference.
- Completeness (Weight 0.2): Coverage of key points.
- Clarity (Weight 0.2): Coherence.

Please first output a single line containing only two values indicating the scores for Assistant 1 and 2, respectively. The two scores are separated by a space.
In the subsequent line, please provide a comprehensive explanation of your evaluation, avoiding any potential bias. 
Finally, output a JSON block with the broken down dimensions.

Output Format:
10.0 <score_for_assistant_2>
<Explanation_Trace>
```json
{{
    "correctness": <0-10>,
    "completeness": <0-10>,
    "clarity": <0-10>
}}
```
            """
            
            response = await self.llm.acomplete(prompt)
            raw_text = response.text.strip()
            self.logger.debug(f"JudgeLM Raw Output: {raw_text[:200]}...")
            
            # Parsing Logic (Robust regex)
            # Pattern 1: Look for "10.0 <score>" at start
            score_match = re.search(r"^10(?:\.0)?\s+(\d+(?:\.\d+)?)", raw_text)
            
            # Pattern 2: Look for JSON block
            json_match = re.search(r"```json(.*?)```", raw_text, re.DOTALL)
            
            final_score = 0.0
            
            if score_match:
                raw_score = float(score_match.group(1))
                final_score = min(1.0, max(0.0, raw_score / 10.0))
            elif json_match:
                # Fallback to JSON if the top line is missing
                try:
                    data = json.loads(json_match.group(1))
                    # Average dimensions if main score missing
                    c = data.get("correctness", 0)
                    cp = data.get("completeness", 0)
                    cl = data.get("clarity", 0)
                    weighted = (c * 0.6) + (cp * 0.2) + (cl * 0.2)
                    final_score = min(1.0, max(0.0, weighted / 10.0))
                except:
                    self.logger.warning("JudgeLM JSON Parse Failed")
                    pass
            
            # Fail safe
            if final_score == 0.0 and "10" not in raw_text:
                 self.logger.warning(f"JudgeLM Parse Failed completely. Raw: {raw_text}")

            return {"success": True, "score": final_score}

        except Exception as e:
            self.logger.error(f"JudgeLM Eval Error: {e}")
            return {"success": False, "score": 0.0}
    
    async def _classify_error(
        self,
        learner_response: str,
        expected_answer: str,
        concept: Dict[str, Any] = None,  # FIX Issue 1: Add concept parameter
        force_real: bool = False
    ) -> Dict[str, Any]:
        """Classify error type with concept context"""
        if self.settings.MOCK_LLM and not force_real:
             return {"success": True, "error_type": "CORRECT" if expected_answer else "CARELESS"}

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
        error_type: ErrorType,
        force_real: bool = False
    ) -> Dict[str, Any]:
        """Detect learner's misconception with reference to known misconceptions"""
        if self.settings.MOCK_LLM and not force_real:
             return {"success": True, "misconception": None}

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
        explanation: str,
        force_real: bool = False
    ) -> Dict[str, Any]:

        """Generate personalized feedback"""
        if self.settings.MOCK_LLM and not force_real:
             return {"success": True, "feedback": "Evaluation Mock: Great job! Your answer matches the expected outcome."}

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
        current_mastery: float,
        concept_difficulty: int = 2,
        error_type: Optional[ErrorType] = None,
        misconception: Optional[str] = None,
        learner_response: str = "",
        expected_answer: str = "",
        concept_name: str = ""
    ) -> float:
        """
        Update learner's mastery using Semantic Knowledge Tracing (LKT).
        
        Scientific Basis: Lee et al. (2024) - Language Model Knowledge Tracing
        - Input: Textual history of interactions.
        - Mechanism: LLM predicts correctness probability for the next step.
        """
        try:
            # 1. Update Interaction History (Append latest)
            # Fetch profile (assuming it contains a 'history' list, if not create one)
            profile = await self.state_manager.get_learner_profile(learner_id) or {}
            history = profile.get("interaction_history", [])
            
            # Create interaction record
            interaction = {
                "concept_name": concept_name or concept_id,
                "question": expected_answer, # Using expected answer as proxy for question text if not provided
                "result": "CORRECT" if score >= 0.8 else "INCORRECT",
                "response": learner_response,
                "timestamp": datetime.now().isoformat()
            }
            history.append(interaction)
            
            # Keep last 10 interactions to fit context window
            if len(history) > 10:
                history = history[-10:]
            
            # Save updated history
            profile["interaction_history"] = history
            # Note: Ideally we'd have a specific method to save the full profile, 
            # but for now we rely on the implementation specific to state_manager.
            # Assuming state_manager has a way to persist this or we save it separately.
            await self.save_state(f"learner_profile:{learner_id}", profile)

            # 2. Format History for LKT
            lkt_history_str = self._format_interaction_history(history)
            
            # 3. Predict Mastery using LKT
            new_mastery = await self._predict_mastery_lkt(
                lkt_history_str,
                target_concept=concept_name or concept_id,
                target_question=expected_answer
            )
            
            # Debug log
            self.logger.debug(
                f"LKT Update: {learner_id}/{concept_id} | "
                f"History Len={len(history)} -> New Mastery={new_mastery:.2f}"
            )
            
            # Save mastery state
            await self.save_state(
                f"learner_mastery:{learner_id}:{concept_id}",
                {"mastery": new_mastery, "updated": datetime.now().isoformat()}
            )
            
            return new_mastery
        
        except Exception as e:
            self.logger.error(f"LKT mastery update error: {e}")
            return current_mastery

    def _format_interaction_history(self, history: List[Dict]) -> str:
        """
        Format history into LKT string:
        [CLS] Concept1 \n Question1 [CORRECT] ... ConceptN \n QuestionN [INCORRECT]
        """
        formatted_segments = ["[CLS]"]
        for entry in history:
            concept = entry.get("concept_name", "Unknown Concept")
            question = entry.get("question", "Unknown Question")
            result = entry.get("result", "INCORRECT") # [CORRECT] or [INCORRECT]
            
            segment = f"{concept} \n {question} [{result}]"
            formatted_segments.append(segment)
            
        return " ".join(formatted_segments)

    async def _predict_mastery_lkt(
        self, 
        history_str: str, 
        target_concept: str,
        target_question: str
    ) -> float:
        """
        Predict mastery probability using LKT Prompting.
        """
        if self.settings.MOCK_LLM:
             return 0.85

        try:
            # Construct the LKT Masked Prompt
            prompt = f"""
            You are a Semantic Knowledge Tracing model (LKT).
            Task: Predict the probability that the student will answer the NEXT question CORRECTLY.
            
            Input Sequence (History):
            {history_str}
            
            Target:
            {target_concept} \n {target_question} [MASK]
            
            Instruction:
            Based on the student's history of correct/incorrect responses and the SEMANTIC RELATIONSHIP between the concepts, estimate the probability (0.00 to 1.00) of the token [CORRECT] filling the [MASK].
            
            Return ONLY the probability float.
            """
            
            response = await self.llm.acomplete(prompt)
            raw_text = response.text.strip()
            
            # Extract float
            import re
            match = re.search(r"0\.\d+|1\.0|0|1", raw_text)
            if match:
                val = float(match.group())
                return max(0.0, min(1.0, val))
            else:
                self.logger.warning(f"LKT did not return float: {raw_text}")
                return 0.5 # Uncertainty fallback
                    
        except Exception as e:
            self.logger.error(f"LKT prediction error: {e}")
            return 0.0
    
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

