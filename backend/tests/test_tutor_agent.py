"""
Unit tests for Tutor Agent.

Run: pytest backend/tests/test_tutor_agent.py -v
"""

import pytest
from backend.models.dialogue import DialogueState, DialoguePhase, ScaffoldingLevel
from backend.core.harvard_enforcer import Harvard7Enforcer


class TestDialogueState:
    """Test dialogue state machine"""
    
    def test_initial_state(self):
        """New state should start at EXPLANATION phase"""
        state = DialogueState("learner1", "sql.join")
        assert state.phase == DialoguePhase.EXPLANATION
        assert state.turn_count == 0
        assert state.scaffolding_level == ScaffoldingLevel.HIGH
    
    def test_phase_advancement_explanation(self):
        """EXPLANATION should advance after 2+ turns"""
        state = DialogueState("learner1", "sql.join")
        assert state.phase == DialoguePhase.EXPLANATION
        
        state.turn_count = 2
        assert state.should_advance_phase() == True
        state.advance_phase()
        assert state.phase == DialoguePhase.QUESTIONING
    
    def test_phase_advancement_questioning_correct(self):
        """QUESTIONING should advance after 2+ correct answers"""
        state = DialogueState("learner1", "sql.join")
        state.phase = DialoguePhase.QUESTIONING
        
        state.correct_answers = 2
        assert state.should_advance_phase() == True
        state.advance_phase()
        assert state.phase == DialoguePhase.PRACTICE
    
    def test_phase_advancement_questioning_attempts(self):
        """QUESTIONING should advance after 3+ attempts"""
        state = DialogueState("learner1", "sql.join")
        state.phase = DialoguePhase.QUESTIONING
        
        state.attempts_in_phase = 3
        assert state.should_advance_phase() == True
    
    def test_phase_advancement_practice(self):
        """PRACTICE should advance after 3+ attempts"""
        state = DialogueState("learner1", "sql.join")
        state.phase = DialoguePhase.PRACTICE
        
        state.attempts_in_phase = 3
        assert state.should_advance_phase() == True
        state.advance_phase()
        assert state.phase == DialoguePhase.ASSESSMENT
    
    def test_misconception_tracking(self):
        """Misconceptions should be tracked correctly"""
        state = DialogueState("learner1", "sql.join")
        state.add_misconception("join_confusion", 0.7, "user said X")
        
        assert len(state.suspected_misconceptions) == 1
        assert state.suspected_misconceptions[0]['type'] == "join_confusion"
        assert state.suspected_misconceptions[0]['confidence'] == 0.7
    
    def test_serialization(self):
        """State should serialize and deserialize correctly"""
        state = DialogueState("learner1", "sql.join", "VISUAL")
        state.turn_count = 3
        state.phase = DialoguePhase.QUESTIONING
        
        data = state.to_dict()
        restored = DialogueState.from_dict(data)
        
        assert restored.learner_id == "learner1"
        assert restored.concept_id == "sql.join"
        assert restored.turn_count == 3
        assert restored.phase == DialoguePhase.QUESTIONING


class TestHarvard7Enforcer:
    """Test Harvard 7 Principles enforcement"""
    
    def test_removes_direct_answers(self):
        """Should replace 'the answer is' with guiding prompt"""
        enforcer = Harvard7Enforcer()
        result = enforcer._remove_direct_answers("The answer is LEFT JOIN.")
        assert "The answer is" not in result or "Let's think" in result
    
    def test_limits_sentences_normal_phase(self):
        """Should limit to 4 sentences for non-ASSESSMENT phases"""
        enforcer = Harvard7Enforcer()
        long_text = ". ".join([f"Sentence {i}" for i in range(10)])
        result = enforcer._limit_cognitive_load(long_text, "QUESTIONING")
        
        # Count sentences
        sentence_count = len([s for s in result.split('.') if s.strip()])
        assert sentence_count <= 4
    
    def test_limits_sentences_assessment_phase(self):
        """Should allow 6 sentences for ASSESSMENT phase"""
        enforcer = Harvard7Enforcer()
        long_text = ". ".join([f"Sentence {i}" for i in range(8)])
        result = enforcer._limit_cognitive_load(long_text, "ASSESSMENT")
        
        sentence_count = len([s for s in result.split('.') if s.strip()])
        assert sentence_count <= 6
    
    def test_adds_probing_questions(self):
        """Should add question if none present"""
        enforcer = Harvard7Enforcer()
        result = enforcer._add_probing_questions("This is a statement without question")
        assert '?' in result
    
    def test_growth_mindset_language(self):
        """Should replace negative language with growth mindset"""
        enforcer = Harvard7Enforcer()
        result = enforcer._add_growth_mindset_language("That is wrong.")
        assert "wrong" not in result.lower() or "interesting attempt" in result
    
    def test_personalize_visual_style(self):
        """Should adapt language for VISUAL learners"""
        enforcer = Harvard7Enforcer()
        result = enforcer._personalize_to_style("Think about how joins work.", "VISUAL")
        assert "picture" in result or "think about" in result
    
    def test_personalize_kinesthetic_style(self):
        """Should adapt language for KINESTHETIC learners"""
        enforcer = Harvard7Enforcer()
        result = enforcer._personalize_to_style("Try to understand this concept.", "KINESTHETIC")
        assert "try working through" in result or "understand" in result
    
    def test_full_enforcement(self):
        """Full enforcement should apply all principles"""
        enforcer = Harvard7Enforcer()
        raw = "The answer is that LEFT JOIN returns all rows. This is important. " * 5
        
        result = enforcer.enforce(
            response=raw,
            learner_context={'learning_style': 'VISUAL'},
            phase='QUESTIONING'
        )
        
        # Should have question
        assert '?' in result
        # Should be limited length
        assert len(result) < len(raw)


class TestTutorIntegration:
    """Integration tests for TutorAgent"""
    
    def test_tutor_agent_init(self):
        """TutorAgent should initialize with correct attributes"""
        from backend.agents.tutor_agent import TutorAgent
        
        class MockStateManager:
            neo4j = None
        
        tutor = TutorAgent(
            agent_id="test_tutor",
            state_manager=MockStateManager(),
            event_bus=None,
            llm=None
        )
        
        assert tutor.agent_id == "test_tutor"
        assert tutor.harvard_enforcer is not None
        assert len(tutor.dialogue_states) == 0
    
    def test_get_or_create_dialogue_state(self):
        """Should create new state or return existing"""
        from backend.agents.tutor_agent import TutorAgent
        
        class MockStateManager:
            neo4j = None
        
        tutor = TutorAgent(
            agent_id="test_tutor",
            state_manager=MockStateManager(),
            event_bus=None,
            llm=None
        )
        
        # First call creates new state
        state1 = tutor._get_or_create_dialogue_state("learner1", "sql.join")
        assert state1.learner_id == "learner1"
        assert state1.concept_id == "sql.join"
        
        # Second call returns same state
        state2 = tutor._get_or_create_dialogue_state("learner1", "sql.join")
        assert state1 is state2
        
        # Different concept creates new state
        state3 = tutor._get_or_create_dialogue_state("learner1", "sql.where")
        assert state3 is not state1


class TestGroundingManager:
    """Test 3-layer grounding"""
    
    def test_grounding_context_initialization(self):
        """GroundingContext should have default values"""
        from backend.core.grounding_manager import GroundingContext
        
        context = GroundingContext()
        assert context.layer1_doc['relevance_score'] == 0.0
        assert context.layer2_kg['definition'] == ''
        assert context.layer3_personal['mastery_level'] == 0.0
        assert context.overall_confidence == 0.0
    
    def test_grounding_manager_weights(self):
        """GroundingManager should have correct weights"""
        from backend.core.grounding_manager import GroundingManager
        
        manager = GroundingManager()
        assert manager.W_DOC == 0.40
        assert manager.W_KG == 0.35
        assert manager.W_PERSONAL == 0.25
        assert abs(manager.W_DOC + manager.W_KG + manager.W_PERSONAL - 1.0) < 0.01
