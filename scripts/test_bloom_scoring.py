
import unittest
import sys
import os
from unittest.mock import MagicMock

# Adjust path to find backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.evaluator_agent import EvaluatorAgent

class TestBloomScoring(unittest.TestCase):
    def setUp(self):
        self.agent = EvaluatorAgent(llm=MagicMock(), embedder=MagicMock(), state_manager=MagicMock())

    def test_bloom_prompt_construction(self):
        """Test that the scoring prompt includes Bloom's Taxonomy instructions"""
        
        # Test Case 1: Low Bloom (Remember)
        # Should ask for Accuracy
        prompt_low = self.agent._construct_scoring_prompt(
            question="Define SQL.",
            learner_response="SQL stands for...",
            expected_answer="Structured Query Language",
            target_bloom=1
        )
        self.assertIn("TARGET COGNITIVE LEVEL: 1", prompt_low)
        self.assertIn("Score on ACCURACY", prompt_low)

    def test_high_bloom_prompt_construction(self):
        """Test that High Bloom (Apply) includes Reasoning constraints"""
        
        # Test Case 2: High Bloom (Apply)
        # Should ask for Reasoning and penalize definition-only answers
        prompt_high = self.agent._construct_scoring_prompt(
            question="Optimize this query.",
            learner_response="I would add an index.",
            expected_answer="Add index on user_id...",
            target_bloom=3
        )
        self.assertIn("TARGET COGNITIVE LEVEL: 3", prompt_high)
        self.assertIn("Score on REASONING", prompt_high)

if __name__ == "__main__":
    unittest.main()
