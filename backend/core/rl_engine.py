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
    LINUCB = "linucb"  # Contextual Bandit (Li et al., 2010)
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
        self.total_reward = 0.0  # Sum of rewards
        self.regret = 0  # Cumulative regret
    
    @property
    def avg_reward(self) -> float:
        """Average reward for this arm"""
        return self.total_reward / self.pulls if self.pulls > 0 else 0.0
    
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
        self.total_reward += reward

    def set_stats(self, pulls: int, total_reward: float) -> None:
        """Restore stats from persistence"""
        self.pulls = pulls
        self.total_reward = total_reward


class LinUCBArm:
    """
    LinUCB Arm with Ridge Regression for Contextual Bandit.
    
    Scientific Basis: Li et al., 2010 - "A Contextual-Bandit Approach to
    Personalized News Article Recommendation" (Yahoo! Research).
    
    Each arm maintains:
    - A: d×d matrix (context covariance)
    - b: d×1 vector (reward accumulator)
    - theta: Ridge regression weights
    """
    
    def __init__(self, concept_id: str, d: int = 10, alpha: float = 1.0):
        """
        Initialize LinUCB arm.
        
        Args:
            concept_id: Concept ID
            d: Context dimension (10-dim profile vector)
            alpha: Exploration parameter (higher = more exploration)
        """
        self.concept_id = concept_id
        self.d = d
        self.alpha = alpha
        
        # Ridge Regression components
        self.A = [[1.0 if i == j else 0.0 for j in range(d)] for i in range(d)]  # d×d identity
        self.b = [0.0] * d  # d×1 zero vector
        self.pulls = 0
    
    def get_ucb_score(self, context: List[float]) -> float:
        """
        Calculate UCB score for this arm given context.
        
        p_a = theta_a^T x + alpha * sqrt(x^T A_a^{-1} x)
        
        Args:
            context: d-dimensional context vector (profile vector)
            
        Returns:
            UCB score (higher = better)
        """
        import numpy as np
        
        x = np.array(context).reshape(-1, 1)  # d×1
        A = np.array(self.A)  # d×d
        b = np.array(self.b).reshape(-1, 1)  # d×1
        
        # Ridge regression: theta = A^{-1} b
        A_inv = np.linalg.inv(A)
        theta = A_inv @ b
        
        # UCB score
        exploitation = float(theta.T @ x)
        exploration = self.alpha * math.sqrt(float(x.T @ A_inv @ x))
        
        return exploitation + exploration
    
    def update(self, context: List[float], reward: float) -> None:
        """
        Update arm statistics after observing reward.
        
        A_a = A_a + x x^T
        b_a = b_a + r x
        
        Args:
            context: Context vector used for selection
            reward: Observed reward (0-1)
        """
        import numpy as np
        
        x = np.array(context).reshape(-1, 1)
        A = np.array(self.A)
        b = np.array(self.b).reshape(-1, 1)
        
        # Update
        A = A + (x @ x.T)
        b = b + (reward * x)
        
        # Store back
        self.A = A.tolist()
        self.b = b.flatten().tolist()
        self.pulls += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize arm state for persistence (Redis)."""
        return {
            "concept_id": self.concept_id,
            "d": self.d,
            "alpha": self.alpha,
            "A": self.A,
            "b": self.b,
            "pulls": self.pulls
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LinUCBArm':
        """Deserialize arm state from persistence."""
        arm = cls(
            concept_id=data["concept_id"],
            d=data.get("d", 10),
            alpha=data.get("alpha", 1.0)
        )
        arm.A = data.get("A", arm.A)
        arm.b = data.get("b", arm.b)
        arm.pulls = data.get("pulls", 0)
        return arm

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
        self.linucb_arms: Dict[str, LinUCBArm] = {}  # Separate storage for LinUCB
        self.time_step = 0
        self.context_dim = 10  # 10-dim profile vector from Agent 2
        self.logger = logging.getLogger(__name__)
    
    def add_arm(self, concept_id: str, difficulty: int) -> None:
        """
        Add a concept (arm) to the bandit problem.
        
        Args:
            concept_id: Concept ID
            difficulty: Difficulty level (1-5)
        """
        if concept_id not in self.arms:
            self.arms[concept_id] = Arm(concept_id, difficulty)
    
    def select_concept(
        self,
        learner_mastery: Dict[str, float],
        prerequisites: Dict[str, List[str]],
        time_available: int,
        learning_style: str,  # NOTE: Encoded in context_vector (Dim 1-4), kept for API compatibility
        candidate_concepts: Optional[List[str]] = None,
        context_vector: Optional[List[float]] = None,
        concept_time_estimates: Optional[Dict[str, float]] = None  # NEW: Filter by time
    ) -> Optional[str]:
        """
        Select next concept for learner to study.
        
        Algorithm:
        1. Filter out concepts already mastered (mastery >= 0.9)
        2. Filter by time estimate (if provided)
        3. Use bandit strategy to select best concept
        
        NOTE: Prerequisites check is done by caller (_get_chain_candidates).
        
        Args:
            learner_mastery: Current mastery level for each concept (0-1)
            prerequisites: Prerequisite relationships (unused - filtered by caller)
            time_available: Hours remaining for time-based filtering
            learning_style: Learner's preferred style (encoded in context_vector)
            candidate_concepts: Optional list of candidate concept IDs to consider
            context_vector: 10-dim profile vector for LinUCB
            concept_time_estimates: Optional dict of concept_id -> estimated_hours
            
        Returns:
            Selected concept ID or None if no eligible concepts
        """
        self.time_step += 1
        
        # Filter eligible concepts
        eligible = []
        concepts_to_check = candidate_concepts if candidate_concepts else list(self.arms.keys())
        for concept_id in concepts_to_check:
            # Skip if already mastered
            current_mastery = learner_mastery.get(concept_id, 0)
            if current_mastery >= 0.9:
                continue
            
            # FIX Issue 3: Filter by time estimate
            if concept_time_estimates and time_available > 0:
                time_estimate = concept_time_estimates.get(concept_id, 0)
                if time_estimate > time_available:
                    continue  # Skip concepts that don't fit in remaining time
            
            eligible.append(concept_id)
        
        if not eligible:
            self.logger.warning("No eligible concepts found")
            return None
        
        # Calculate rewards for each eligible concept
        rewards = {}
        for concept_id in eligible:
            arm = self.arms.get(concept_id)
            if not arm:
                # If arm doesn't exist yet, create it with default difficulty
                self.add_arm(concept_id, 2)
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
        elif self.strategy == BanditStrategy.LINUCB:
            if context_vector is None:
                self.logger.warning("LinUCB requires context_vector, falling back to UCB")
                selected = self._ucb(eligible)
            else:
                selected = self._linucb(eligible, context_vector)
        else:
            selected = random.choice(eligible)
        
        self.logger.info(f"Selected concept: {selected} (strategy: {self.strategy.value})")
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
    
    def _linucb(self, eligible: List[str], context: List[float]) -> str:
        """
        LinUCB selection: select concept with highest contextual UCB score.
        
        Uses Ridge Regression to learn context-reward relationship.
        Scientific Basis: Li et al., 2010 (Yahoo! Research).
        """
        best_concept = None
        best_score = -float('inf')
        
        for concept_id in eligible:
            # Get or create LinUCB arm
            if concept_id not in self.linucb_arms:
                self.linucb_arms[concept_id] = LinUCBArm(
                    concept_id, 
                    d=self.context_dim
                )
            
            arm = self.linucb_arms[concept_id]
            score = arm.get_ucb_score(context)
            
            if score > best_score:
                best_score = score
                best_concept = concept_id
        
        return best_concept
    
    def record_feedback(self, concept_id: str, evaluation_score: float, context_vector: Optional[List[float]] = None) -> None:
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
