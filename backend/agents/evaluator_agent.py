import logging
import uuid
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
from llama_index.llms.gemini import Gemini

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
        self.decision_engine = DecisionEngine(
            personal_kg=personal_kg
        )
        
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
            learner_id = kwargs.get("learner_id")
            concept_id = kwargs.get("concept_id")
            learner_response = kwargs.get("learner_response")
            expected_answer = kwargs.get("expected_answer")
            correct_answer_explanation = kwargs.get("correct_answer_explanation", "")
            
            if not all([learner_id, concept_id, learner_response]):
                return {
                    "success": False,
                    "error": "learner_id, concept_id, learner_response required",
                    "agent_id": self.agent_id
                }
            
            self.logger.info(f"📊 Evaluating {learner_id} on {concept_id}")
            
            # Step 1: Get concept details
            neo4j = self.state_manager.neo4j
            concept_result = await neo4j.run_query(
                "MATCH (c:CourseConcept {concept_id: $concept_id}) RETURN c",
                concept_id=concept_id
            )
            
            if not concept_result:
                return {
                    "success": False,
                    "error": f"Concept not found: {concept_id}",
                    "agent_id": self.agent_id
                }
            
            concept = concept_result[0].get("c", {})
            
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
                # Step 3: Classify error
                error_result = await self._classify_error(
                    learner_response=learner_response,
                    expected_answer=expected_answer
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
            await self.send_message(
                receiver="path_planner",
                message_type="evaluation_complete",
                payload={
                    "learner_id": learner_id,
                    "concept_id": concept_id,
                    "score": score,
                    "decision": decision.value,
                    "new_mastery": new_mastery
                }
            )
            
            self.logger.info(f"✅ Evaluation complete: {error_type.value} ({score:.1%})")
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ Evaluation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    async def _score_response(
        self,
        learner_response: str,
        expected_answer: str,
        explanation: str
    ) -> Dict[str, Any]:
        """Score learner response (0-1)"""
        try:
            prompt = f"""
            Score this learner response.
            
            Question: (learner is answering about a concept)
            Learner response: {learner_response}
            Expected answer: {expected_answer}
            Correct explanation: {explanation}
            
            Return ONLY a JSON with "score" (0-1 float).
            0 = completely wrong
            0.5 = partially correct
            1 = completely correct
            
            Example: {{"score": 0.8}}
            """
            
            response = await self.llm.acomplete(prompt)
            score_text = response.text
            
            # Parse score from JSON
            try:
                # Try to extract JSON
                import re
                match = re.search(r'"score"\s*:\s*([\d.]+)', score_text)
                if match:
                    score = float(match.group(1))
                else:
                    # Fallback: simple comparison
                    score = 0.8 if learner_response.lower() in expected_answer.lower() else 0.2
                score = max(0.0, min(1.0, score))  # Clamp to 0-1
            except:
                score = 0.0 if learner_response.lower() != expected_answer.lower() else 1.0
            
            return {"success": True, "score": score}
        
        except Exception as e:
            self.logger.error(f"Scoring error: {e}")
            return {"success": False, "score": 0.0}
    
    async def _classify_error(
        self,
        learner_response: str,
        expected_answer: str
    ) -> Dict[str, Any]:
        """Classify error type"""
        try:
            prompt = f"""
            Classify this error:
            
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
                error_type = "CONCEPTUAL"  # Default to worst case
            
            return {"success": True, "error_type": error_type}
        
        except Exception as e:
            self.logger.error(f"Error classification error: {e}")
            return {"success": False, "error_type": "CONCEPTUAL"}
    
    async def _detect_misconception(
        self,
        learner_response: str,
        concept: Dict[str, Any],
        error_type: ErrorType
    ) -> Dict[str, Any]:
        """Detect learner's misconception"""
        try:
            if error_type == ErrorType.CORRECT:
                return {"success": True, "misconception": None}
            
            concept_name = concept.get("name", "Unknown")
            
            prompt = f"""
            What misconception does this learner have?
            
            Concept: {concept_name}
            Learner response: {learner_response}
            
            Identify the mistaken belief or mental model.
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
            feedback = response.text.strip()
            
            return {"success": True, "feedback": feedback}
        
        except Exception as e:
            self.logger.error(f"Feedback generation error: {e}")
            return {"success": False, "feedback": "Let's review this concept together."}
    
    async def _make_path_decision(
        self,
        score: float,
        current_mastery: float,
        error_type: ErrorType,
        concept_difficulty: int
    ) -> PathDecision:
        """
        Make decision for next learning action (per Thesis).
        
        Decision Logic:
        - score > 0.85 -> MASTERED or PROCEED
        - score > 0.6 -> ALTERNATE (try different example)
        - score < 0.6 + CONCEPTUAL error -> REMEDIATE (go to prerequisites)
        - else -> RETRY (same concept, new question)
        """
        
        if score >= 0.9:
            return PathDecision.MASTERED
        elif score >= 0.85:
            return PathDecision.PROCEED
        elif score >= 0.6:
            # Good enough but not perfect - try different angle
            return PathDecision.ALTERNATE
        else:
            # Low score - check error type
            if error_type == ErrorType.CONCEPTUAL:
                # Fundamental misunderstanding - need prerequisites
                return PathDecision.REMEDIATE
            else:
                # Careless/Incomplete/Procedural - retry with new question
                return PathDecision.RETRY
    
    async def _update_learner_mastery(
        self,
        learner_id: str,
        concept_id: str,
        score: float,
        current_mastery: float
    ) -> float:
        """Update learner's mastery level"""
        try:
            # Weighted average of current mastery and new score
            weight = 0.6  # New score is 60% of update
            new_mastery = (current_mastery * (1 - weight)) + (score * weight)
            
            # Save to database
            await self.save_state(
                f"learner_mastery:{learner_id}:{concept_id}",
                {"mastery": new_mastery, "updated": datetime.now().isoformat()}
            )
            
            return new_mastery
        
        except Exception as e:
            self.logger.error(f"Mastery update error: {e}")
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
            result = await self.execute(
                learner_id=learner_id,
                concept_id=concept_id,
                learner_response=event.get('learner_answer', ''),
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

