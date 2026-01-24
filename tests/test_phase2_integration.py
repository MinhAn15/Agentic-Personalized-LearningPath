
import unittest
import numpy as np
import sys
import os
sys.path.append(os.getcwd())

from backend.evaluation.learning_metrics import LearningOutcomeAnalyzer, LearnerOutcomeMetrics
from backend.synthetic_data.learner_generator import LearnerGenerator, SyntheticLearner

class TestPhase2Integration(unittest.TestCase):
    
    def test_learning_gain_calculation(self):
        """Verify normalized gain calculation matches theoretical values"""
        # Case 1: Standard gain
        m = LearnerOutcomeMetrics(
            learner_id="1", course_id="c1",
            pre_test_score=20, post_test_score=60,
            time_to_mastery_min=100, retention_test_score=50,
            error_distribution={}
        )
        # Gain = (60 - 20) / (100 - 20) = 40/80 = 0.5
        self.assertAlmostEqual(m.learning_gain, 0.5)
        
        # Case 2: Negative gain
        m2 = LearnerOutcomeMetrics(
            learner_id="2", course_id="c1",
            pre_test_score=50, post_test_score=40,
            time_to_mastery_min=100, retention_test_score=40,
            error_distribution={}
        )
        # Gain = (40 - 50) / (100 - 50) = -10/50 = -0.2
        self.assertAlmostEqual(m2.learning_gain, -0.2)
        
    def test_effect_size_calculation(self):
        """Verify Cohen's d calculation"""
        # Group 1: Mean=5, SD=1
        # Group 2: Mean=3, SD=1
        # d should be ~2.0
        
        g1 = [4, 5, 6] # Mean 5, Var 1
        g2 = [2, 3, 4] # Mean 3, Var 1
        
        result = LearningOutcomeAnalyzer.effect_size(g1, g2)
        d = result["cohens_d"]
        
        self.assertTrue(1.9 < d < 2.1, f"Expected d approx 2.0, got {d}")
        self.assertEqual(result["interpretation"], "large")
        
    def test_learner_generator(self):
        """Verify synthetic learner creation"""
        learner = LearnerGenerator.create_synthetic_learner("test_course")
        self.assertTrue(0 <= learner.profile["overall_mastery"] <= 1)
        self.assertIn(learner.profile["learning_style"], ["VISUAL", "TEXTUAL", "KINESTHETIC"])
        
        # Simulation response
        resp = LearnerGenerator.simulate_learner_response(learner, "prompt", 0.5)
        self.assertTrue(isinstance(resp, str))
        self.assertTrue(len(resp) > 5)

if __name__ == "__main__":
    unittest.main()
