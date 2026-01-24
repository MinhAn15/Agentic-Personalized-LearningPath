import random
import uuid
import numpy as np
from typing import List, Dict, Any, Optional

class SyntheticLearner:
    """Represents a synthetic learner with profile and state"""
    
    def __init__(self, learner_id: str, profile: Dict, course_id: str = "course_1"):
        self.id = learner_id
        self.course_id = course_id
        self.profile = profile
        self.mastery: Dict[str, float] = {}
        self.history: List[Dict] = []
        self.total_time_spent = 0
        self.error_histogram = {"CONCEPTUAL": 0, "COMPUTATIONAL": 0, "PROCEDURAL": 0}

class LearnerGenerator:
    """Generates synthetic learner profiles for A/B testing"""
    
    @staticmethod
    def create_synthetic_learner(course_id: str = "cs101") -> SyntheticLearner:
        """Create a randomized learner profile"""
        learner_id = str(uuid.uuid4())[:8]
        
        # Randomize traits
        mastery_base = np.random.beta(2, 5)  # Skewed towards 0.3-0.5
        learning_style = random.choice(["VISUAL", "TEXTUAL", "KINESTHETIC"])
        motivation = random.uniform(0.1, 1.0)
        
        profile = {
            "learner_id": learner_id,
            "overall_mastery": mastery_base,
            "learning_style": learning_style,
            "motivation": motivation,
            "time_available": random.randint(10, 60), # Hours
            "hours_per_day": random.uniform(0.5, 4.0),
            "preferred_content_types": [
                "VIDEO" if learning_style == "VISUAL" else "ARTICLE"
            ],
            "goals": ["mastery"]
        }
        
        return SyntheticLearner(learner_id, profile, course_id)
    
    @staticmethod
    def simulate_learner_response(learner: SyntheticLearner, prompt: str, difficulty: float) -> str:
        """
        Simulate a response string based on learner mastery vs difficulty.
        Returns a string that might be correct or contain errors.
        """
        # simplified probability model
        # P(correct) = sigmoid(mastery - difficulty)
        mastery = learner.profile["overall_mastery"]
        prob_correct = 1 / (1 + np.exp(-5 * (mastery - difficulty * 0.2))) # difficulty normalized 0-1 approx?
        
        if random.random() < prob_correct:
            return "The correct answer is [Simulation of correct logic]. Key concept applied correctly."
        else:
            # Simulate error
            error_type = random.choice(["CONCEPTUAL", "COMPUTATIONAL", "PROCEDURAL"])
            learner.error_histogram[error_type] += 1
            return f"I think it is [Wrong Answer]. because [Flawed Logic ({error_type})]."

    @staticmethod
    def administer_assessment(learner: SyntheticLearner, assessment_type: str) -> float:
        """
        Simulate taking a test.
        Returns score 0-100.
        """
        base_ability = learner.profile["overall_mastery"]
        boost = 0.0
        
        if assessment_type == "post_test":
            # Assume learning happened? (This is tricky, usually the simulation updates mastery)
            # In our simulation loop, mastery should have increased.
            # We use the 'mastery' dict to calculate average mastery gain
            if learner.mastery:
                avg_mastery = sum(learner.mastery.values()) / len(learner.mastery)
                base_ability = max(base_ability, avg_mastery)
                
        elif assessment_type == "retention_test":
            # Apply decay based on time/motivation (simplified)
            decay = random.uniform(0.05, 0.15)
            base_ability = base_ability * (1 - decay)
            
        # Add some noise
        score = base_ability * 100 + np.random.normal(0, 5)
        return max(0, min(100, score))
