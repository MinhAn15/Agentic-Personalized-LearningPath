
import unittest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.evaluator_agent import EvaluatorAgent
from backend.models.evaluation import ErrorType

class TestAgent2_HybridDKT(unittest.TestCase):
    """
    Verification for Agent 2 (Evaluator) - Hybrid DKT-LLM Logic.
    """
    
    def setUp(self):
        # Mock dependencies
        self.mock_llm = AsyncMock()
        self.mock_state_manager = MagicMock()
        self.mock_event_bus = MagicMock()
        
        # Initialize Agent
        self.agent = EvaluatorAgent(
            agent_id="test_opt_2", 
            state_manager=self.mock_state_manager, 
            event_bus=self.mock_event_bus,
            llm=self.mock_llm
        )
        
        # Suppress logging during tests
        self.agent.logger = MagicMock()

    def test_community_prior_calculation(self):
        """Test that cold start prior is derived from difficulty"""
        # Difficulty 1 (Easy) -> Expect High Prior (e.g., 0.85)
        # Logic: 1.0 - (1 * 0.15) = 0.85
        prior_easy = 1.0 - (1 * self.agent.DKT_PRIOR_WEIGHT)
        self.assertEqual(prior_easy, 0.85)
        
        # Difficulty 5 (Hard) -> Expect Low Prior (e.g., 0.25)
        # Logic: 1.0 - (5 * 0.15) = 0.25
        prior_hard = 1.0 - (5 * self.agent.DKT_PRIOR_WEIGHT)
        self.assertEqual(prior_hard, 0.25)

    def test_hybrid_llm_update_success(self):
        """Test that LLM output is correctly parsed into mastery"""
        # Mock LLM to return a mastery float
        self.mock_llm.acomplete.return_value = MagicMock(text="0.75")
        
        prior = 0.5
        current = 0.4
        context = "Test Context"
        
        # Run async test
        new_mastery = asyncio.run(self.agent._calculate_hybrid_mastery(
            prior, current, context, is_correct=True
        ))
        
        self.assertEqual(new_mastery, 0.75, "Should parse float from LLM response")
        
        # Verify prompt contained inputs
        call_args = self.mock_llm.acomplete.call_args[0][0]
        self.assertIn(f"{prior:.2f}", call_args)
        self.assertIn(f"{current:.2f}", call_args)

    def test_hybrid_llm_fallback(self):
        """Test fallback when LLM output is invalid"""
        # Mock LLM to return garbage
        self.mock_llm.acomplete.return_value = MagicMock(text="I am not sure")
        
        current = 0.5
        # Correct answer fallback: current + step_size (0.1)
        expected = min(1.0, current + self.agent.DKT_STEP_SIZE)
        
        new_mastery = asyncio.run(self.agent._calculate_hybrid_mastery(
            prior=0.5, current=current, context="ctx", is_correct=True
        ))
        
        self.assertEqual(new_mastery, expected, "Should use fallback step size on LLM failure")

    def test_full_update_flow(self):
        """Verify integration from _update_learner_mastery to _calculate_hybrid_mastery"""
        # Mock internal calculation to isolate flow
        self.agent._calculate_hybrid_mastery = AsyncMock(return_value=0.88)
        self.agent.save_state = AsyncMock()
        
        asyncio.run(self.agent._update_learner_mastery(
            learner_id="student_1",
            concept_id="concept_A",
            score=0.9,
            current_mastery=0.4,
            concept_difficulty=2, # imply Prior = 1.0 - 0.3 = 0.7
            error_type=None
        ))
        
        # Verify inputs passed to calculation
        self.agent._calculate_hybrid_mastery.assert_called_once()
        args = self.agent._calculate_hybrid_mastery.call_args
        prior_arg = args[0][0]
        
        # Check Prior Calculation
        self.assertAlmostEqual(prior_arg, 0.7, places=2)
        
        # Check Save State
        self.agent.save_state.assert_called_once()

if __name__ == "__main__":
    unittest.main()
