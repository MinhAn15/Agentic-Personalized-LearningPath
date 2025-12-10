"""
Evaluator Agent

Responsible for:
- Assessing learner knowledge and skills
- Generating adaptive assessments
- Providing detailed feedback
- Tracking mastery levels
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import logging
import random

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.event_bus import EventType, Event

logger = logging.getLogger(__name__)


class QuestionType(str, Enum):
    """Types of assessment questions"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    CODE = "code"
    ESSAY = "essay"
    MATCHING = "matching"


class BloomLevel(str, Enum):
    """Bloom's Taxonomy levels for questions"""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


@dataclass
class Question:
    """Assessment question"""
    question_id: str
    concept_id: str
    question_type: QuestionType
    bloom_level: BloomLevel
    text: str
    options: Optional[List[str]] = None
    correct_answer: Optional[Any] = None
    explanation: str = ""
    difficulty: float = 0.5
    points: int = 1
    
    def to_dict(self) -> Dict:
        return {
            "question_id": self.question_id,
            "concept_id": self.concept_id,
            "question_type": self.question_type.value,
            "bloom_level": self.bloom_level.value,
            "text": self.text,
            "options": self.options,
            "difficulty": self.difficulty,
            "points": self.points
        }
    
    def to_dict_with_answer(self) -> Dict:
        data = self.to_dict()
        data["correct_answer"] = self.correct_answer
        data["explanation"] = self.explanation
        return data


@dataclass
class Assessment:
    """Complete assessment"""
    assessment_id: str
    user_id: str
    concept_ids: List[str]
    questions: List[Question]
    time_limit: int  # minutes
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    
    def to_dict(self) -> Dict:
        return {
            "assessment_id": self.assessment_id,
            "user_id": self.user_id,
            "concept_ids": self.concept_ids,
            "questions": [q.to_dict() for q in self.questions],
            "time_limit": self.time_limit,
            "created_at": self.created_at.isoformat(),
            "status": self.status
        }


@dataclass
class AssessmentResult:
    """Assessment result with detailed feedback"""
    assessment_id: str
    user_id: str
    score: float
    total_points: int
    earned_points: int
    time_taken: int  # seconds
    question_results: List[Dict]
    feedback: Dict[str, Any]
    completed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "assessment_id": self.assessment_id,
            "user_id": self.user_id,
            "score": self.score,
            "total_points": self.total_points,
            "earned_points": self.earned_points,
            "time_taken": self.time_taken,
            "question_results": self.question_results,
            "feedback": self.feedback,
            "completed_at": self.completed_at.isoformat()
        }


class EvaluatorAgent(BaseAgent):
    """
    Agent responsible for learner assessment and evaluation.
    
    Features:
    - Adaptive question selection (IRT-based)
    - Bloom's Taxonomy alignment
    - Detailed feedback generation
    - Mastery-based progression
    
    Assessment Types:
    - Diagnostic (pre-learning)
    - Formative (during learning)
    - Summative (post-learning)
    """
    
    def __init__(
        self,
        agent_id: str,
        state_manager: Any,
        event_bus: Any,
        llm: Optional[Any] = None
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.EVALUATOR,
            state_manager=state_manager,
            event_bus=event_bus
        )
        self.llm = llm
        self.assessments: Dict[str, Assessment] = {}
        self.question_bank: Dict[str, List[Question]] = {}
        
        # Initialize mock question bank
        self._init_question_bank()
    
    def _init_question_bank(self):
        """Initialize mock question bank"""
        # Would be loaded from database in production
        pass
    
    async def execute(
        self,
        user_id: str,
        action: str = "create_assessment",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute evaluator actions.
        
        Args:
            user_id: The learner's ID
            action: Action to perform (create_assessment, submit_answer,
                   grade_assessment, get_feedback)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing action results
        """
        self.logger.info(f"📝 Evaluator action: {action} for user {user_id}")
        
        try:
            if action == "create_assessment":
                return await self._create_assessment(user_id, **kwargs)
            
            elif action == "get_question":
                return await self._get_question(user_id, **kwargs)
            
            elif action == "submit_answer":
                return await self._submit_answer(user_id, **kwargs)
            
            elif action == "grade_assessment":
                return await self._grade_assessment(user_id, **kwargs)
            
            elif action == "get_feedback":
                return await self._get_feedback(user_id, **kwargs)
            
            elif action == "adaptive_question":
                return await self._get_adaptive_question(user_id, **kwargs)
            
            else:
                return {"status": "error", "error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"❌ Evaluator action failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _create_assessment(
        self,
        user_id: str,
        concept_ids: List[str],
        assessment_type: str = "formative",
        num_questions: int = 5,
        time_limit: int = 15,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new assessment"""
        
        import hashlib
        assessment_id = hashlib.md5(
            f"{user_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Generate questions
        questions = self._generate_questions(
            concept_ids, 
            num_questions,
            assessment_type
        )
        
        assessment = Assessment(
            assessment_id=assessment_id,
            user_id=user_id,
            concept_ids=concept_ids,
            questions=questions,
            time_limit=time_limit,
            status="active"
        )
        
        self.assessments[assessment_id] = assessment
        await self.save_state(f"assessment:{assessment_id}", assessment.to_dict())
        
        self.logger.info(
            f"✅ Created assessment {assessment_id} with {len(questions)} questions"
        )
        
        return {
            "status": "success",
            "assessment_id": assessment_id,
            "questions": [q.to_dict() for q in questions],
            "time_limit": time_limit
        }
    
    def _generate_questions(
        self,
        concept_ids: List[str],
        num_questions: int,
        assessment_type: str
    ) -> List[Question]:
        """Generate questions for assessment"""
        
        questions = []
        
        for i in range(num_questions):
            concept_id = concept_ids[i % len(concept_ids)]
            
            # Vary question types and bloom levels
            q_type = random.choice(list(QuestionType)[:3])  # MC, T/F, Short
            bloom = self._select_bloom_level(assessment_type, i, num_questions)
            
            question = self._create_mock_question(
                question_id=f"q_{i}",
                concept_id=concept_id,
                q_type=q_type,
                bloom=bloom
            )
            questions.append(question)
        
        return questions
    
    def _select_bloom_level(
        self, 
        assessment_type: str,
        question_index: int,
        total_questions: int
    ) -> BloomLevel:
        """Select Bloom's level based on assessment type and position"""
        
        levels = list(BloomLevel)
        
        if assessment_type == "diagnostic":
            # Focus on lower levels
            return random.choice(levels[:3])
        elif assessment_type == "formative":
            # Mix of levels
            return random.choice(levels[:4])
        else:  # summative
            # Include higher levels
            progress = question_index / total_questions
            if progress < 0.3:
                return random.choice(levels[:2])
            elif progress < 0.7:
                return random.choice(levels[1:4])
            else:
                return random.choice(levels[2:])
    
    def _create_mock_question(
        self,
        question_id: str,
        concept_id: str,
        q_type: QuestionType,
        bloom: BloomLevel
    ) -> Question:
        """Create a mock question"""
        
        if q_type == QuestionType.MULTIPLE_CHOICE:
            return Question(
                question_id=question_id,
                concept_id=concept_id,
                question_type=q_type,
                bloom_level=bloom,
                text=f"Which of the following best describes {concept_id}?",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer="Option A",
                explanation=f"Option A is correct because...",
                difficulty=0.5
            )
        
        elif q_type == QuestionType.TRUE_FALSE:
            return Question(
                question_id=question_id,
                concept_id=concept_id,
                question_type=q_type,
                bloom_level=bloom,
                text=f"Statement about {concept_id}: True or False?",
                options=["True", "False"],
                correct_answer="True",
                explanation="This is true because...",
                difficulty=0.3
            )
        
        else:  # SHORT_ANSWER
            return Question(
                question_id=question_id,
                concept_id=concept_id,
                question_type=q_type,
                bloom_level=bloom,
                text=f"Explain the concept of {concept_id} in your own words.",
                correct_answer=None,  # Requires LLM grading
                explanation="A good answer should include...",
                difficulty=0.7
            )
    
    async def _get_question(
        self,
        user_id: str,
        assessment_id: str,
        question_index: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """Get a specific question from assessment"""
        
        if assessment_id not in self.assessments:
            return {"status": "error", "error": "Assessment not found"}
        
        assessment = self.assessments[assessment_id]
        
        if question_index >= len(assessment.questions):
            return {"status": "completed", "message": "All questions answered"}
        
        question = assessment.questions[question_index]
        
        return {
            "status": "success",
            "question": question.to_dict(),
            "question_number": question_index + 1,
            "total_questions": len(assessment.questions)
        }
    
    async def _submit_answer(
        self,
        user_id: str,
        assessment_id: str,
        question_id: str,
        answer: Any,
        time_spent: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """Submit answer for a question"""
        
        if assessment_id not in self.assessments:
            return {"status": "error", "error": "Assessment not found"}
        
        assessment = self.assessments[assessment_id]
        
        # Find question
        question = None
        for q in assessment.questions:
            if q.question_id == question_id:
                question = q
                break
        
        if not question:
            return {"status": "error", "error": "Question not found"}
        
        # Grade answer
        is_correct = self._grade_answer(question, answer)
        
        # Store result
        result_key = f"answer:{assessment_id}:{question_id}"
        await self.save_state(result_key, {
            "answer": answer,
            "is_correct": is_correct,
            "time_spent": time_spent,
            "submitted_at": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "is_correct": is_correct,
            "explanation": question.explanation if not is_correct else "Correct!",
            "correct_answer": question.correct_answer if not is_correct else None
        }
    
    def _grade_answer(self, question: Question, answer: Any) -> bool:
        """Grade a single answer"""
        
        if question.question_type in [
            QuestionType.MULTIPLE_CHOICE, 
            QuestionType.TRUE_FALSE
        ]:
            return answer == question.correct_answer
        
        elif question.question_type == QuestionType.SHORT_ANSWER:
            # Would use LLM for grading
            # For now, simple keyword check
            return len(str(answer)) > 10
        
        return False
    
    async def _grade_assessment(
        self,
        user_id: str,
        assessment_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Grade complete assessment"""
        
        if assessment_id not in self.assessments:
            return {"status": "error", "error": "Assessment not found"}
        
        assessment = self.assessments[assessment_id]
        
        # Collect all answers
        question_results = []
        earned_points = 0
        total_points = 0
        
        for question in assessment.questions:
            result_key = f"answer:{assessment_id}:{question.question_id}"
            answer_data = await self.load_state(result_key)
            
            if answer_data:
                is_correct = answer_data.get("is_correct", False)
                points = question.points if is_correct else 0
            else:
                is_correct = False
                points = 0
            
            earned_points += points
            total_points += question.points
            
            question_results.append({
                "question_id": question.question_id,
                "concept_id": question.concept_id,
                "bloom_level": question.bloom_level.value,
                "is_correct": is_correct,
                "points_earned": points,
                "points_possible": question.points
            })
        
        score = earned_points / total_points if total_points > 0 else 0
        
        # Generate feedback
        feedback = self._generate_feedback(question_results, score)
        
        # Create result
        result = AssessmentResult(
            assessment_id=assessment_id,
            user_id=user_id,
            score=score,
            total_points=total_points,
            earned_points=earned_points,
            time_taken=0,
            question_results=question_results,
            feedback=feedback
        )
        
        # Update assessment status
        assessment.status = "graded"
        await self.save_state(f"result:{assessment_id}", result.to_dict())
        
        # Publish event
        await self.event_bus.publish(Event(
            event_type=EventType.USER_ASSESSMENT,
            source=self.agent_id,
            payload={
                "user_id": user_id,
                "assessment_id": assessment_id,
                "score": score
            }
        ))
        
        self.logger.info(
            f"✅ Graded assessment {assessment_id}: {score:.1%}"
        )
        
        return {
            "status": "success",
            "result": result.to_dict()
        }
    
    def _generate_feedback(
        self, 
        question_results: List[Dict],
        score: float
    ) -> Dict[str, Any]:
        """Generate detailed feedback"""
        
        # Analyze by concept
        concept_performance = {}
        for result in question_results:
            concept = result["concept_id"]
            if concept not in concept_performance:
                concept_performance[concept] = {"correct": 0, "total": 0}
            concept_performance[concept]["total"] += 1
            if result["is_correct"]:
                concept_performance[concept]["correct"] += 1
        
        # Identify weak areas
        weak_areas = [
            concept for concept, perf in concept_performance.items()
            if perf["correct"] / perf["total"] < 0.5
        ]
        
        # Generate recommendations
        if score >= 0.8:
            message = "Excellent work! You've demonstrated strong mastery."
            recommendation = "Ready to advance to the next level."
        elif score >= 0.6:
            message = "Good progress! Some areas need more practice."
            recommendation = "Review the concepts you missed before continuing."
        else:
            message = "Keep learning! Review the material and try again."
            recommendation = "Focus on the fundamentals before advancing."
        
        return {
            "overall_message": message,
            "recommendation": recommendation,
            "concept_performance": concept_performance,
            "weak_areas": weak_areas,
            "mastery_achieved": score >= 0.8
        }
    
    async def _get_feedback(
        self,
        user_id: str,
        assessment_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Get feedback for assessment"""
        
        result = await self.load_state(f"result:{assessment_id}")
        
        if not result:
            return {"status": "error", "error": "Result not found"}
        
        return {
            "status": "success",
            "feedback": result.get("feedback", {})
        }
    
    async def _get_adaptive_question(
        self,
        user_id: str,
        concept_id: str,
        current_ability: float = 0.5,
        **kwargs
    ) -> Dict[str, Any]:
        """Get adaptive question based on learner ability (IRT-based)"""
        
        # Select difficulty near learner ability
        target_difficulty = current_ability + random.uniform(-0.1, 0.1)
        target_difficulty = max(0.1, min(0.9, target_difficulty))
        
        # Create question at target difficulty
        question = self._create_mock_question(
            question_id=f"adaptive_{datetime.now().timestamp()}",
            concept_id=concept_id,
            q_type=QuestionType.MULTIPLE_CHOICE,
            bloom=BloomLevel.UNDERSTAND
        )
        question.difficulty = target_difficulty
        
        return {
            "status": "success",
            "question": question.to_dict(),
            "target_difficulty": target_difficulty
        }
