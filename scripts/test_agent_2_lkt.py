
import unittest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.evaluator_agent import EvaluatorAgent

class TestAgent2_LKT(unittest.TestCase):
    """
    Verification for Agent 2 (Evaluator) - Semantic LKT Logic.
    """
    
    def setUp(self):
        # Mock dependencies
        self.mock_llm = AsyncMock()
        self.mock_state_manager = MagicMock()
        self.mock_event_bus = MagicMock()
        
        # Initialize Agent
        self.agent = EvaluatorAgent(
            agent_id="test_lkt_2", 
            state_manager=self.mock_state_manager, 
            event_bus=self.mock_event_bus,
            llm=self.mock_llm
        )
        # Suppress logging
        self.agent.logger = MagicMock()

    def test_format_interaction_history(self):
        """Test LKT history string formatting"""
        history = [
            {"concept_name": "Math", "question": "1+1?", "result": "CORRECT"},
            {"concept_name": "Physics", "question": "Force?", "result": "INCORRECT"}
        ]
        
        expected = "[CLS] Math \n 1+1? [CORRECT] Physics \n Force? [INCORRECT]"
        actual = self.agent._format_interaction_history(history)
        
        self.assertEqual(actual.strip(), expected.strip())

    def test_lkt_prediction_success(self):
        """Test LKT LLM response parsing"""
        # Mock LLM response
        self.mock_llm.acomplete.return_value = MagicMock(text="Probability: 0.85")
        
        score = asyncio.run(self.agent._predict_mastery_lkt(
            history_str="[CLS] ...",
            target_concept="Algebra",
            target_question="Solve X"
        ))
        
        self.assertEqual(score, 0.85, "Should parse 0.85 float")
        
        # Verify prompt structure
        call_args = self.mock_llm.acomplete.call_args[0][0]
        self.assertIn("Semantic Knowledge Tracing model (LKT)", call_args)
        self.assertIn("Algebra", call_args)

    def test_lkt_prediction_fallback(self):
        """Test fallback when LLM output is malformed"""
        self.mock_llm.acomplete.return_value = MagicMock(text="I don't know")
        
        score = asyncio.run(self.agent._predict_mastery_lkt(
            history_str="...", target_concept="X", target_question="Y"
        ))
        
        self.assertEqual(score, 0.5, "Should return 0.5 uncertainty on failure")

    def test_full_update_flow(self):
        """Test _update_learner_mastery integration"""
        # Mock State Manager profile return
        self.mock_state_manager.get_learner_profile = AsyncMock(return_value={"interaction_history": []})
        self.agent.save_state = AsyncMock()
        
        # Mock internal prediction to isolate flow
        self.agent._predict_mastery_lkt = AsyncMock(return_value=0.95)
        
        new_mastery = asyncio.run(self.agent._update_learner_mastery(
            learner_id="student_1",
            concept_id="concept_X",
            score=1.0,
            current_mastery=0.5,
            concept_name="Integration",
            expected_answer="Area under curve"
        ))
        
        # Verify flow
        # 1. Profile fetched
        self.mock_state_manager.get_learner_profile.assert_called_with("student_1")
        
        # 2. History formatted and passed to predict
        self.agent._predict_mastery_lkt.assert_called()
        
        # 3. State saved
        self.agent.save_state.assert_called()
        
        self.assertEqual(new_mastery, 0.95)

if __name__ == "__main__":
    unittest.main()
