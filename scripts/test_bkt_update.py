
import unittest
import sys
import os

# Adjust path to find backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.evaluator_agent import EvaluatorAgent

class TestBKTUpdate(unittest.TestCase):
    def setUp(self):
        # Mock dependencies (not needed/used for the static method test, but good practice)
        self.agent = EvaluatorAgent(llm=None, embedder=None, state_manager=None)

    def test_learning_gain(self):
        """Test that correct answer increases mastery (Learning)"""
        prior = 0.5
        posterior = self.agent._update_learner_mastery(prior, is_correct=True)
        print(f"BKT Learn: {prior} -> {posterior}")
        self.assertTrue(posterior > prior, "Mastery should increase after success")

    def test_slipping(self):
        """Test that incorrect answer on high mastery decreases mastery slightly (Slipping)"""
        prior = 0.95
        posterior = self.agent._update_learner_mastery(prior, is_correct=False)
        print(f"BKT Slip: {prior} -> {posterior}")
        self.assertTrue(posterior < prior, "Mastery should decrease after failure")
        self.assertTrue(posterior > 0.6, "High mastery should mostly slip, not crash to zero")

    def test_guessing(self):
        """Test that low mastery increases SLOWLY on success (Guessing penalty)"""
        prior = 0.1
        posterior_correct = self.agent._update_learner_mastery(prior, is_correct=True)
        gain = posterior_correct - prior
        print(f"BKT Guess Gain: {gain}")
        
        # Compare with a high mastery gain
        prior_high = 0.5
        posterior_high = self.agent._update_learner_mastery(prior_high, is_correct=True)
        gain_high = posterior_high - prior_high
        
        # In BKT, usually P(Learn) applies equally, BUT the bayesian update for low prior 
        # is dampened by P(Guess) = 0.25. 
        # P(Correct|Know)=0.9, P(Correct|~Know)=0.25 (Guess)
        # If I don't know (0.1), correctness is likely a Guess, so posterior shouldn't jump too high.
        self.assertTrue(gain < 0.5, "Gain from low mastery should not be instant mastery")

if __name__ == "__main__":
    unittest.main()
