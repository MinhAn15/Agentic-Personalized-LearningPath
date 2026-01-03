
import unittest
import sys
import os
from datetime import datetime, timedelta

# Adjust path to find backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.path_planner_agent import PathPlannerAgent

class TestSpacedRepetition(unittest.TestCase):
    def setUp(self):
        self.agent = PathPlannerAgent(llm=None, embedder=None, state_manager=None)

    def test_high_priority_decay(self):
        """Test that a high mastery concept reviewed long ago has HIGH priority (Exponential Decay)"""
        mastery = 0.9
        # Reviewed 60 days ago
        last_review = datetime.now() - timedelta(days=60)
        
        priority = self.agent._calculate_review_priority(mastery, last_review)
        print(f"High Mastery (0.9), 60 days ago -> Priority: {priority}")
        
        # Should be high because retention has dropped
        self.assertTrue(priority > 0.3, "High mastery should eventually need review")

    def test_low_priority_recent(self):
        """Test that a recently reviewed concept has LOW priority"""
        mastery = 0.8
        # Reviewed 1 day ago
        last_review = datetime.now() - timedelta(days=1)
        
        priority = self.agent._calculate_review_priority(mastery, last_review)
        print(f"Mastery (0.8), 1 day ago -> Priority: {priority}")
        
        self.assertTrue(priority < 0.1, "Recent review should have very low priority")

    def test_remediation_vs_review(self):
        """Test distinction between Remediation (Low Mastery) and Review (Decay)"""
        # Case A: Low Mastery (Need Remediation) - Handled by normal path logic, but here we test Review Priority
        mastery_low = 0.2
        last_review = datetime.now() - timedelta(days=1)
        priority_low = self.agent._calculate_review_priority(mastery_low, last_review)
        
        # Case B: High Mastery (Need Review)
        mastery_high = 0.95
        last_review_old = datetime.now() - timedelta(days=100)
        priority_high = self.agent._calculate_review_priority(mastery_high, last_review_old)
        
        print(f"Remediation Priority: {priority_low} vs Review Priority: {priority_high}")
        
        # Scientific Basis: Spaced Repetition targets forgetting (High), not learning (Low)
        self.assertTrue(priority_high > priority_low, "Review system should prioritize decaying high mastery over low mastery")

if __name__ == "__main__":
    unittest.main()
