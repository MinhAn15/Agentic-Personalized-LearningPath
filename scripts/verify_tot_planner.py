
import asyncio
import logging
import random
from typing import List, Dict
import pytest
from unittest.mock import AsyncMock, MagicMock

import sys
import os
sys.path.append(os.getcwd())

# Import Agent
from backend.agents.path_planner_agent import PathPlannerAgent
from backend.models import LearnerProfile

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Planner_ToT_Test")

class MockStateManager:
    def __init__(self):
        self.redis = MagicMock()
        self.redis.pipeline.return_value = MagicMock()
        self.redis.pipeline.return_value.execute = AsyncMock(return_value=[])

class MockEventBus:
    def __init__(self):
        self.subscribe = MagicMock()
        self.publish = AsyncMock()

class MockLLM:
    """Mock LLM for ToT Evaluation"""
    async def acomplete(self, prompt: str) -> MagicMock:
        response = MagicMock()
        # Mock logic: favor paths with "easy" -> "hard"
        if "easy -> medium -> hard" in prompt:
            response.text = "Score: 0.9 (Good progression)"
        elif "hard -> easy" in prompt:
            response.text = "Score: 0.2 (Bad prerequisite)"
        else:
            response.text = f"Score: {random.uniform(0.4, 0.7)}"
        return response

async def verify_tot_planner():
    """Verify Tree of Thoughts (Beam Search) Logic"""
    logger.info("\n🧪 1. Initializing Path Planner (Mock Mode)...")
    
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    llm = MockLLM()
    
    agent = PathPlannerAgent("planner_test", state_manager, event_bus, llm=llm)
    agent.llm = llm # Force inject
    
    # Mock Graph reachable concepts
    # Graph:
    # START -> [A, B, C]
    # A (Easy) -> [A1, A2] -> [A3]
    # B (Hard) -> [B1] -> [B2]
    # C (Medium) -> [C1] -> [C2]
    
    async def mock_get_reachable(learner_id, concept_id, limit=5):
        graph = {
            "START": ["concept_A_easy", "concept_B_hard", "concept_C_med"],
            "concept_A_easy": ["concept_A_med", "concept_A_alt"],
            "concept_A_med": ["concept_A_hard"],
            "concept_B_hard": ["concept_B_very_hard"],
            "concept_C_med": ["concept_C_hard"]
        }
        return graph.get(concept_id, [])

    agent._get_reachable_concepts = mock_get_reachable
    
    # =========================================================================
    # TEST CASE 1: Thought Generation (Beam Expansion)
    # =========================================================================
    logger.info("\n🧪 TEST CASE 1: Beam Search Expansion")
    
    # Start from START
    initial_candidates = ["concept_A_easy", "concept_B_hard", "concept_C_med"]
    
    best_path = await agent._explore_learning_paths("learner_1", initial_candidates, current_concept="START")
    
    logger.info(f"Result Path: {best_path}")
    
    # We expect the planner to choose the "Easy -> Medium -> Hard" path (A chain) 
    # because our MockLLM gives it 0.9 score.
    
    path_str = " -> ".join(best_path)
    if "concept_A" in path_str:
         logger.info("✅ ToT Selected Logical Path (A_easy -> A_med)")
    else:
         logger.info("❌ ToT Failed to select optimal path")

    # =========================================================================
    # TEST CASE 2: Pruning (Evaluating Bad Paths)
    # =========================================================================
    logger.info("\n🧪 TEST CASE 2: Evaluation Scoring")
    
    score_good = await agent._evaluate_path_viability("l1", ["easy", "medium", "hard"])
    score_bad = await agent._evaluate_path_viability("l1", ["hard", "easy"])
    
    logger.info(f"Score Good Path: {score_good}")
    logger.info(f"Score Bad Path: {score_bad}")
    
    if score_good > score_bad:
        logger.info("✅ Evaluator correctly ranked logical path higher")
    else:
        logger.error("❌ Evaluator ranking failed")

if __name__ == "__main__":
    asyncio.run(verify_tot_planner())
