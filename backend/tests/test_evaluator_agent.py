"""
Unit tests for Evaluator Agent.

Run: pytest backend/tests/test_evaluator_agent.py -v
"""

import pytest
from backend.models.evaluation import ErrorType, PathDecision, Misconception, EvaluationResult


class TestEvaluationModels:
    """Test evaluation data models"""
    
    def test_error_type_values(self):
        """ErrorType should have 5 values"""
        assert len(ErrorType) == 5
        assert ErrorType.CORRECT.value == "CORRECT"
        assert ErrorType.CONCEPTUAL.value == "CONCEPTUAL"
    
    def test_path_decision_values(self):
        """PathDecision should have 5 values"""
        assert len(PathDecision) == 5
        assert PathDecision.MASTERED.value == "MASTERED"
        assert PathDecision.REMEDIATE.value == "REMEDIATE"
    
    def test_misconception_creation(self):
        """Misconception should create with defaults"""
        m = Misconception(
            type="join_vs_filter",
            description="Confuses WHERE with JOIN"
        )
        assert m.type == "join_vs_filter"
        assert m.severity == "MEDIUM"
        assert m.confidence == 0.7
        assert m.frequency == 1
    
    def test_misconception_to_dict(self):
        """Misconception should serialize correctly"""
        m = Misconception(
            type="test_type",
            description="Test description",
            severity="HIGH",
            confidence=0.9
        )
        d = m.to_dict()
        assert d['type'] == "test_type"
        assert d['severity'] == "HIGH"
        assert d['confidence'] == 0.9
    
    def test_evaluation_result_creation(self):
        """EvaluationResult should create with defaults"""
        result = EvaluationResult(
            learner_id="learner1",
            concept_id="sql.where",
            learner_answer="SELECT * FROM users",
            expected_answer="SELECT * FROM users WHERE id > 5"
        )
        assert result.learner_id == "learner1"
        assert result.score == 0.0
        assert result.error_type == ErrorType.CORRECT
        assert result.decision == PathDecision.PROCEED
    
    def test_evaluation_result_mastery_gain(self):
        """mastery_gain property should calculate correctly"""
        result = EvaluationResult(
            learner_id="l1", concept_id="c1",
            learner_answer="a", expected_answer="b"
        )
        result.mastery_before = 0.5
        result.mastery_after = 0.7
        assert result.mastery_gain == 0.2


class TestSemanticScorer:
    """Test semantic scoring"""
    
    @pytest.mark.asyncio
    async def test_perfect_match_high_score(self):
        """Identical answers should score near 1.0"""
        from backend.core.semantic_scorer import SemanticScorer
        
        scorer = SemanticScorer()
        learner = "SELECT * FROM users WHERE id > 5"
        expected = "SELECT * FROM users WHERE id > 5"
        
        score, confidence = await scorer.score_answer("sql.where", learner, expected, {})
        assert score >= 0.8
    
    @pytest.mark.asyncio
    async def test_empty_answer_zero_score(self):
        """Empty answer should score 0.0"""
        from backend.core.semantic_scorer import SemanticScorer
        
        scorer = SemanticScorer()
        score, confidence = await scorer.score_answer("sql.where", "", "SELECT * FROM users", {})
        assert score == 0.0
        assert confidence >= 0.5


class TestErrorClassifier:
    """Test error classification"""
    
    @pytest.mark.asyncio
    async def test_high_score_correct(self):
        """Score >= 0.95 should classify as CORRECT"""
        from backend.core.error_classifier import ErrorClassifier
        
        classifier = ErrorClassifier()
        error_type, misconceptions = await classifier.classify(
            "SELECT * FROM users", 
            "SELECT * FROM users", 
            0.98, 
            "sql.select"
        )
        assert error_type == ErrorType.CORRECT
        assert len(misconceptions) == 0
    
    @pytest.mark.asyncio
    async def test_typo_careless(self):
        """Minor typo should classify as CARELESS"""
        from backend.core.error_classifier import ErrorClassifier
        
        classifier = ErrorClassifier()
        error_type, _ = await classifier.classify(
            "SELEC * FROM users",  # Typo
            "SELECT * FROM users",
            0.85,
            "sql.select"
        )
        assert error_type == ErrorType.CARELESS
    
    @pytest.mark.asyncio
    async def test_low_score_conceptual(self):
        """Very low score + low similarity should indicate CONCEPTUAL error"""
        from backend.core.error_classifier import ErrorClassifier
        
        classifier = ErrorClassifier()
        error_type, _ = await classifier.classify(
            "JOIN combines columns",  # Wrong concept
            "WHERE filters rows",
            0.25,
            "sql.where"
        )
        # Should be PROCEDURAL or CONCEPTUAL (depends on similarity)
        assert error_type in [ErrorType.PROCEDURAL, ErrorType.CONCEPTUAL, ErrorType.INCOMPLETE]


class TestMasteryTracker:
    """Test mastery tracking"""
    
    @pytest.mark.asyncio
    async def test_mastery_update_formula(self):
        """Mastery should update with weighted average formula"""
        from backend.core.mastery_tracker import MasteryTracker
        
        tracker = MasteryTracker()
        
        # Formula: mastery_new = (1 - 0.3) * 0 + 0.3 * 0.8 = 0.24
        # With Bloom boost for high score: +0.05 if score >= 0.9
        # Without boost (score=0.8): 0.24
        
        # Note: Without personal_kg, mastery_old = 0
        mastery = await tracker.update_mastery("l1", "c1", 0.8, "APPLY")
        
        # 0.3 * 0.8 = 0.24 (no boost since score < 0.9)
        assert 0.2 <= mastery <= 0.3
    
    @pytest.mark.asyncio
    async def test_bloom_boost_high_score(self):
        """High score should get Bloom boost"""
        from backend.core.mastery_tracker import MasteryTracker
        
        tracker = MasteryTracker()
        
        # Score 0.95 with APPLY Bloom level should get +0.05 boost
        mastery = await tracker.update_mastery("l1", "c1", 0.95, "APPLY")
        
        # 0.3 * 0.95 + 0.05 = 0.285 + 0.05 = 0.335
        assert mastery >= 0.3


class TestDecisionEngine:
    """Test path decision logic"""
    
    @pytest.mark.asyncio
    async def test_perfect_mastery_mastered(self):
        """Mastery >= 0.9 without severe misconceptions should be MASTERED"""
        from backend.core.decision_engine import DecisionEngine
        
        engine = DecisionEngine()
        decision = await engine.decide(
            mastery_new=0.95,
            error_type=ErrorType.CORRECT,
            misconceptions=[],
            learner_id="l1",
            concept_id="c1"
        )
        assert decision == PathDecision.MASTERED
    
    @pytest.mark.asyncio
    async def test_good_mastery_proceed(self):
        """Mastery >= 0.8 without conceptual error should be PROCEED"""
        from backend.core.decision_engine import DecisionEngine
        
        engine = DecisionEngine()
        decision = await engine.decide(
            mastery_new=0.85,
            error_type=ErrorType.CARELESS,
            misconceptions=[],
            learner_id="l1",
            concept_id="c1"
        )
        assert decision == PathDecision.PROCEED
    
    @pytest.mark.asyncio
    async def test_conceptual_error_remediate(self):
        """Conceptual error with low mastery should REMEDIATE"""
        from backend.core.decision_engine import DecisionEngine
        
        engine = DecisionEngine()
        misconceptions = [Misconception(
            type="join_vs_filter",
            description="Confuses WHERE with JOIN",
            severity="HIGH"
        )]
        
        decision = await engine.decide(
            mastery_new=0.35,
            error_type=ErrorType.CONCEPTUAL,
            misconceptions=misconceptions,
            learner_id="l1",
            concept_id="c1"
        )
        assert decision == PathDecision.REMEDIATE
    
    @pytest.mark.asyncio
    async def test_moderate_with_conceptual_alternate(self):
        """Moderate mastery + conceptual error should try ALTERNATE"""
        from backend.core.decision_engine import DecisionEngine
        
        engine = DecisionEngine()
        misconceptions = [Misconception(
            type="concept_confusion",
            description="Test",
            severity="HIGH"
        )]
        
        decision = await engine.decide(
            mastery_new=0.65,
            error_type=ErrorType.CONCEPTUAL,
            misconceptions=misconceptions,
            learner_id="l1",
            concept_id="c1"
        )
        # Should be ALTERNATE or RETRY
        assert decision in [PathDecision.ALTERNATE, PathDecision.RETRY]


class TestEvaluatorIntegration:
    """Integration tests for EvaluatorAgent"""
    
    def test_evaluator_init(self):
        """EvaluatorAgent should initialize with core modules"""
        from backend.agents.evaluator_agent import EvaluatorAgent
        
        class MockStateManager:
            neo4j = None
        
        evaluator = EvaluatorAgent(
            agent_id="test_evaluator",
            state_manager=MockStateManager(),
            event_bus=None
        )
        
        assert evaluator.agent_id == "test_evaluator"
        assert evaluator.scorer is not None
        assert evaluator.classifier is not None
        assert evaluator.tracker is not None
        assert evaluator.decision_engine is not None
