from typing import Dict, List, Any, Optional
from enum import Enum
import random
import math
import logging

logger = logging.getLogger(__name__)

class BanditStrategy(str, Enum):
    """Bandit selection strategies"""
    EPSILON_GREEDY = "epsilon_greedy"
    UCB = "ucb"  # Upper Confidence Bound
    THOMPSON = "thompson"

class Arm:
    """
    Single arm in multi-armed bandit.
    Represents a concept in learning path.
    """
    
    def __init__(self, concept_id: str, difficulty: int):
        """
        Initialize arm.
        
        Args:
            concept_id: Concept ID
            difficulty: Difficulty level (1-5)
        """
        self.concept_id = concept_id
        self.difficulty = difficulty
        self.pulls = 0  # Number of times selected
        self.rewards = []  # Rewards from each pull
        self.regret = 0  # Cumulative regret
    
    @property
    def avg_reward(self) -> float:
        """Average reward for this arm"""
        return sum(self.rewards) / len(self.rewards) if self.rewards else 0
    
    def ucb_score(self, t: int) -> float:
        """
        Upper Confidence Bound score.
        Balances exploitation (high reward) with exploration (uncertainty)
        """
        if self.pulls == 0:
            return float('inf')
        
        exploitation = self.avg_reward
        exploration = math.sqrt(2 * math.log(t) / self.pulls)
        return exploitation + exploration
    
    def pull(self, reward: float) -> None:
        """
        Record a pull of this arm.
        
        Args:
            reward: Reward received
        """
        self.pulls += 1
        self.rewards.append(reward)

class RLEngine:
    """
    Reinforcement Learning engine for path planning.
    
    Implements multi-armed bandit to select optimal learning sequence.
    """
    
    def __init__(self, strategy: BanditStrategy = BanditStrategy.UCB, epsilon: float = 0.1):
        """
        Initialize RL engine.
        
        Args:
            strategy: Bandit selection strategy
            epsilon: Exploration rate (for epsilon-greedy)
        """
        self.strategy = strategy
        self.epsilon = epsilon
        self.arms: Dict[str, Arm] = {}
        self.time_step = 0
        self.logger = logging.getLogger(__name__)
    
    def add_arm(self, concept_id: str, difficulty: int) -> None:
        """
        Add a concept (arm) to the bandit problem.
        
        Args:
            concept_id: Concept ID
            difficulty: Difficulty level (1-5)
        """
        self.arms[concept_id] = Arm(concept_id, difficulty)
    
    def select_concept(
        self,
        learner_mastery: Dict[str, float],
        prerequisites: Dict[str, List[str]],
        time_available: int,
        learning_style: str
    ) -> Optional[str]:
        """
        Select next concept for learner to study.
        
        Algorithm:
        1. Filter out concepts where prerequisites not met
        2. Filter out concepts already mastered (mastery >= 0.9)
        3. Calculate reward for each eligible concept
        4. Use bandit strategy to select best concept
        
        Args:
            learner_mastery: Current mastery level for each concept (0-1)
            prerequisites: Prerequisite relationships {concept: [required_concepts]}
            time_available: Hours remaining
            learning_style: Learner's preferred style (VISUAL, AUDITORY, etc.)
            
        Returns:
            Selected concept ID or None if no eligible concepts
        """
        self.time_step += 1
        
        # Filter eligible concepts
        eligible = []
        for concept_id, arm in self.arms.items():
            # Skip if already mastered
            current_mastery = learner_mastery.get(concept_id, 0)
            if current_mastery >= 0.9:
                continue
            
            # Check prerequisites
            required = prerequisites.get(concept_id, [])
            prerequisites_met = all(
                learner_mastery.get(req, 0) >= 0.7 for req in required
            )
            if not prerequisites_met:
                continue
            
            eligible.append(concept_id)
        
        if not eligible:
            self.logger.warning("No eligible concepts found")
            return None
        
        # Calculate rewards for each eligible concept
        rewards = {}
        for concept_id in eligible:
            arm = self.arms[concept_id]
            current_mastery = learner_mastery.get(concept_id, 0)
            
            # Reward = improvement potential × difficulty match
            improvement_potential = 1.0 - current_mastery  # 0-1
            difficulty_match = 1.0 - abs(arm.difficulty / 5.0 - 0.5)  # 0-1
            
            base_reward = improvement_potential * difficulty_match
            rewards[concept_id] = base_reward
        
        # Select using bandit strategy
        if self.strategy == BanditStrategy.EPSILON_GREEDY:
            selected = self._epsilon_greedy(eligible, rewards)
        elif self.strategy == BanditStrategy.UCB:
            selected = self._ucb(eligible)
        else:
            selected = random.choice(eligible)
        
        self.logger.info(f"Selected concept: {selected}")
        return selected
    
    def _epsilon_greedy(self, eligible: List[str], rewards: Dict[str, float]) -> str:
        """
        Epsilon-greedy selection: exploit best with probability 1-epsilon,
        explore random with probability epsilon.
        """
        if random.random() < self.epsilon:
            # Explore: random selection
            return random.choice(eligible)
        else:
            # Exploit: select concept with highest reward
            return max(eligible, key=lambda c: rewards[c])
    
    def _ucb(self, eligible: List[str]) -> str:
        """
        UCB selection: select concept with highest upper confidence bound.
        Balances exploitation and exploration mathematically.
        """
        best_concept = None
        best_score = -float('inf')
        
        for concept_id in eligible:
            arm = self.arms[concept_id]
            score = arm.ucb_score(self.time_step)
            
            if score > best_score:
                best_score = score
                best_concept = concept_id
        
        return best_concept
    
    def record_feedback(self, concept_id: str, evaluation_score: float) -> None:
        """
        Record learner's performance on a concept.
        
        Args:
            concept_id: Concept ID
            evaluation_score: Score from evaluation (0-1)
        """
        if concept_id not in self.arms:
            self.logger.warning(f"Unknown concept: {concept_id}")
            return
        
        arm = self.arms[concept_id]
        arm.pull(evaluation_score)
        self.logger.info(f"Feedback recorded: {concept_id} = {evaluation_score}")
