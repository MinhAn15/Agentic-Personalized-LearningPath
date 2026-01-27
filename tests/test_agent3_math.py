import pytest
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import MagicMock, AsyncMock, patch
from backend.agents.path_planner_agent import PathPlannerAgent, ChainingMode

@pytest.mark.asyncio
async def test_reward_function_dropout_penalty():
    """
    Test Case 1 (The Math):
    Verify that high dropout risk results in a significant penalty in the reward calculation.
    Formula: r_t = (alpha * mastery) + (beta * completion) - (gamma * dropout_risk)
    
    If dropout_risk is high (0.8), reward should be significantly lower, potentially negative.
    """
    # 1. Setup Agent and Mocks
    mock_state_manager = MagicMock()
    mock_event_bus = MagicMock()
    mock_redis = AsyncMock()
    mock_state_manager.redis = mock_redis
    
    # Mock Redis lock to work with the agent's check
    mock_lock = MagicMock()
    # Define a proper async method for acquire
    async def async_acquire():
        return True
    
    # Make acquire a proper coroutine function so iscoroutinefunction returns True (or use MagicMock that behaves)
    # The agent checks if asyncio.iscoroutinefunction(redis_lock.acquire). 
    # To satisfy this check simply, we can just use a real async function or make the mock look like one.
    # However, an easier way is to just let it fall to 'else' and return True.
    # If we make acquire a regular MagicMock (not AsyncMock) that returns True, 
    # iscoroutinefunction is False, so it calls synchronous acquire(), which returns True.
    mock_lock.acquire = MagicMock(return_value=True) 
    # Ensure iscoroutinefunction returns False for this mock
    
    # redis.lock must be synchronous to return the lock object immediately
    mock_redis.lock = MagicMock(return_value=mock_lock)
    
    mock_llm = AsyncMock()
    agent = PathPlannerAgent("agent-3", mock_state_manager, mock_event_bus, llm=mock_llm)
    
    # 2. Mock Data
    concept_id = "CONCEPT_X"
    score = 0.5 # Moderate mastery
    passed = True
    dropout_risk = 0.8 # HIGH RISK
    
    # Mock Redis get for existing MAB stats (to avoid errors)
    mock_redis.get.return_value = None 
    
    # 3. Simulate Evaluation Feedback Event with Dropout Risk
    # NOTE: The current code does NOT use 'dropout_risk' from the event.
    # This test expects the code to be updated to look for it.
    event_payload = {
        "concept_id": concept_id,
        "score": score,
        "passed": passed,
        "dropout_risk": dropout_risk, # <--- The new input
        "context_vector": [0.1] * 10
    }
    
    # Mock internal methods to isolate reward logic if possible, 
    # but _on_evaluation_feedback is the entry point. 
    # We need to capture the 'reward' variable inside the method.
    # Since we can't easily spy on local variables, we will verify the side effect:
    # The updated 'total_reward' sent to Redis or the log message if we capture logs.
    
    # We'll use a patch on the redis.set to inspect the value being saved.
    
    await agent._on_evaluation_feedback(event_payload)
    
    # 4. Assertions
    # We expect redis.set to be called with updated stats.
    # The 'total_reward' should reflect the penalty.
    # Standard Reward w/o penalty: (0.6 * 0.5) + (0.4 * 1.0) = 0.3 + 0.4 = 0.7
    # Expected Penalty w/ Gamma=0.5 (example): 0.7 - (0.5 * 0.8) = 0.3
    # If Gamma=1.0: 0.7 - 0.8 = -0.1 (NEGATIVE)
    
    # Find the call to redis.set for "mab_stats:CONCEPT_X"
    call_args_list = mock_redis.set.call_args_list
    mab_call = None
    for args, kwargs in call_args_list:
        if args[0] == f"mab_stats:{concept_id}":
            mab_call = args
            break
            
    assert mab_call is not None, "Redis set not called for MAB stats"
    
    import json
    data = json.loads(mab_call[1])
    saved_reward = data["total_reward"]
    
    # The Assertion: 
    # Current code hardcodes dropout_penalty = 0.0, so reward would be 0.7
    # We assert it is significantly LESS than 0.7 (implying penalty was applied)
    # or specifically check for negative if we enforce high gamma.
    print(f"Calculated Reward: {saved_reward}")
    
    # Using a threshold. If penalty is ignored, this will exceed 0.6.
    # If penalty is applied (assuming gamma > 0.5), it should be < 0.5.
    assert saved_reward < 0.5, f"Reward {saved_reward} is too high! Dropout penalty ignored."


@pytest.mark.asyncio
async def test_hard_prerequisite_constraint():
    """
    Test Case 2 (The Constraint):
    Verify that if a prerequisite is missing in Neo4j, path evaluation fails (score 0.0),
    ignoring any LLM hallucination.
    """
    # 1. Setup
    mock_state_manager = MagicMock()
    mock_neo4j = AsyncMock()
    mock_state_manager.neo4j = mock_neo4j
    
    # Removed invalid test_mode argument
    mock_llm = AsyncMock()
    agent = PathPlannerAgent("agent-3", state_manager=mock_state_manager, event_bus=MagicMock(), llm=mock_llm)
    
    # 2. Mock Scenario
    learner_id = "learner_123"
    path = ["Current_Node", "Target_Node"]
    
    # Mock Neo4j to return "1" count for missing prerequisites.
    # Query logic: RETURN count(prereq) -> if > 0, means missing prereqs exist.
    async def mock_run_query(query, **kwargs):
        # Relaxed check: Just look for the core relationship key
        if "REQUIRES" in query and "missing_count" in query:
             # Simulate finding 1 missing prerequisite
             return [{"missing_count": 1}]
        return []
    
    mock_neo4j.run_query.side_effect = mock_run_query
    
    # 3. Execution
    # Calling _evaluate_path_viability which should now include the hard check
    score = await agent._evaluate_path_viability(learner_id, path)
    
    # 4. Assertion
    # Should be 0.0 because of hard constraint violation
    assert score == 0.0, f"Score {score} should be 0.0 due to missing prerequisite!"
