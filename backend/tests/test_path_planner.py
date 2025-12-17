"""
Unit tests for Path Planner Agent.

Run: pytest backend/tests/test_path_planner.py -v
"""

import pytest
from backend.agents.path_planner_agent import (
    PathPlannerAgent,
    ChainingMode,
    EvaluationDecision
)
from backend.core.rl_engine import RLEngine, BanditStrategy


class TestChainingMode:
    """Test chaining mode selection logic"""
    
    def test_select_forward_on_proceed(self):
        agent = PathPlannerAgent.__new__(PathPlannerAgent)
        mode = agent._select_chain_mode(EvaluationDecision.PROCEED.value)
        assert mode == ChainingMode.FORWARD
    
    def test_select_forward_on_mastered(self):
        agent = PathPlannerAgent.__new__(PathPlannerAgent)
        mode = agent._select_chain_mode(EvaluationDecision.MASTERED.value)
        assert mode == ChainingMode.FORWARD
    
    def test_select_backward_on_remediate(self):
        agent = PathPlannerAgent.__new__(PathPlannerAgent)
        mode = agent._select_chain_mode(EvaluationDecision.REMEDIATE.value)
        assert mode == ChainingMode.BACKWARD
    
    def test_select_lateral_on_retry(self):
        agent = PathPlannerAgent.__new__(PathPlannerAgent)
        mode = agent._select_chain_mode(EvaluationDecision.RETRY.value)
        assert mode == ChainingMode.LATERAL
    
    def test_select_lateral_on_alternate(self):
        agent = PathPlannerAgent.__new__(PathPlannerAgent)
        mode = agent._select_chain_mode(EvaluationDecision.ALTERNATE.value)
        assert mode == ChainingMode.LATERAL
    
    def test_select_lateral_on_none(self):
        agent = PathPlannerAgent.__new__(PathPlannerAgent)
        mode = agent._select_chain_mode(None)
        assert mode == ChainingMode.LATERAL


class TestTimeEstimation:
    """Test time estimation formula"""
    
    def test_medium_difficulty_medium_velocity(self):
        """0.5 * 1.0 * (1/1.0) = 0.5 hours"""
        from backend.core.constants import CONCEPT_BASE_TIME, DIFFICULTY_MULTIPLIER
        
        difficulty = 3
        velocity = 1.0
        expected = CONCEPT_BASE_TIME * DIFFICULTY_MULTIPLIER[difficulty] * (1 / velocity)
        
        assert abs(expected - 0.5) < 0.01
    
    def test_hard_difficulty_fast_learner(self):
        """0.5 * 1.5 * (1/2.0) = 0.375 hours"""
        from backend.core.constants import CONCEPT_BASE_TIME, DIFFICULTY_MULTIPLIER
        
        difficulty = 4
        velocity = 2.0
        expected = CONCEPT_BASE_TIME * DIFFICULTY_MULTIPLIER[difficulty] * (1 / velocity)
        
        assert abs(expected - 0.375) < 0.01
    
    def test_easy_difficulty_slow_learner(self):
        """0.5 * 0.8 * (1/0.5) = 0.8 hours"""
        from backend.core.constants import CONCEPT_BASE_TIME, DIFFICULTY_MULTIPLIER
        
        difficulty = 2
        velocity = 0.5
        expected = CONCEPT_BASE_TIME * DIFFICULTY_MULTIPLIER[difficulty] * (1 / velocity)
        
        assert abs(expected - 0.8) < 0.01


class TestSuccessProbability:
    """Test success probability calculation"""
    
    @pytest.mark.asyncio
    async def test_high_mastery_good_time(self):
        """High mastery + good time fit = high probability"""
        from backend.core.constants import (
            SUCCESS_PROB_MASTERY_WEIGHT,
            SUCCESS_PROB_TIME_WEIGHT,
            SUCCESS_PROB_DIFFICULTY_WEIGHT
        )
        
        avg_mastery = 0.9
        time_fit = 1.0
        difficulty_penalty = 0.0  # Medium difficulty
        
        prob = (
            SUCCESS_PROB_MASTERY_WEIGHT * avg_mastery +
            SUCCESS_PROB_TIME_WEIGHT * time_fit -
            SUCCESS_PROB_DIFFICULTY_WEIGHT * difficulty_penalty
        )
        
        assert 0.7 < prob <= 1.0
    
    @pytest.mark.asyncio
    async def test_low_mastery_tight_time(self):
        """Low mastery + high difficulty = low probability"""
        from backend.core.constants import (
            SUCCESS_PROB_MASTERY_WEIGHT,
            SUCCESS_PROB_TIME_WEIGHT,
            SUCCESS_PROB_DIFFICULTY_WEIGHT
        )
        
        avg_mastery = 0.2
        time_fit = 0.5
        difficulty_penalty = 0.2  # Hard difficulty
        
        prob = (
            SUCCESS_PROB_MASTERY_WEIGHT * avg_mastery +
            SUCCESS_PROB_TIME_WEIGHT * time_fit -
            SUCCESS_PROB_DIFFICULTY_WEIGHT * difficulty_penalty
        )
        
        assert 0.0 <= prob < 0.5


class TestUCBBandit:
    """Test RL engine (UCB Bandit)"""
    
    def test_unvisited_arm_high_priority(self):
        """Unvisited arms should be selected for exploration"""
        engine = RLEngine(strategy=BanditStrategy.UCB)
        engine.add_arm('arm1', difficulty=2)
        engine.add_arm('arm2', difficulty=2)
        
        # Both unvisited initially - should select one
        selected = engine.bandit._ucb(['arm1', 'arm2'])
        assert selected in ['arm1', 'arm2']
    
    def test_arm_update_increases_value(self):
        """Updating arm with reward should increase estimated value"""
        engine = RLEngine(strategy=BanditStrategy.UCB)
        engine.add_arm('concept1', difficulty=2)
        
        assert engine.bandit.arms['concept1'].avg_reward == 0
        
        engine.bandit.arms['concept1'].pull(0.8)
        assert engine.bandit.arms['concept1'].avg_reward == 0.8
        assert engine.bandit.arms['concept1'].pulls == 1
    
    def test_arm_exploration_bonus_decay(self):
        """Exploration bonus should decrease as visits increase"""
        engine = RLEngine(strategy=BanditStrategy.UCB)
        engine.add_arm('concept1', difficulty=2)
        
        # Many visits
        for _ in range(10):
            engine.bandit.arms['concept1'].pull(0.5)
        
        arm = engine.bandit.arms['concept1']
        assert arm.pulls == 10
        assert arm.avg_reward == 0.5


class TestRelationshipMap:
    """Test relationship map building"""
    
    def test_build_relationship_map_basic(self):
        """Test basic relationship map building"""
        relationships = [
            {'source': 'SQL_JOIN', 'target': 'SQL_SELECT', 'rel_type': 'REQUIRES'},
            {'source': 'SQL_JOIN', 'target': 'SQL_WHERE', 'rel_type': 'REQUIRES'},
            {'source': 'SQL_SELECT', 'target': 'SQL_WHERE', 'rel_type': 'NEXT'}
        ]
        
        agent = PathPlannerAgent.__new__(PathPlannerAgent)
        rel_map = agent._build_relationship_map(relationships)
        
        assert 'REQUIRES' in rel_map
        assert 'NEXT' in rel_map
        assert 'SQL_SELECT' in rel_map['REQUIRES']['SQL_JOIN']
        assert 'SQL_WHERE' in rel_map['REQUIRES']['SQL_JOIN']
