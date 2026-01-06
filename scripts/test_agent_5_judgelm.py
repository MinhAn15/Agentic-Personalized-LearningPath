
import asyncio
import sys
import os
import unittest
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.evaluator_agent import EvaluatorAgent

class TestAgent5JudgeLM(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.mock_event_bus = MagicMock()
        self.mock_state_manager = MagicMock()
        
        self.agent = EvaluatorAgent(
            agent_id="eval_test",
            state_manager=self.mock_state_manager,
            event_bus=self.mock_event_bus,
            llm=self.mock_llm
        )
    
    def test_score_judgelm_structure(self):
        """Verify strict PROMPT structure is generated (Figure 5)"""
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Mock LLM Response (Ideal Case)
        self.mock_llm.acomplete = AsyncMock(return_value=MagicMock(text="""10.0 8.5
The student answer is mostly correct but misses the 'JOIN' distinction.
```json
{
    "correctness": 9,
    "completeness": 8,
    "clarity": 8
}
```
"""))

        result = loop.run_until_complete(self.agent._score_response(
            learner_response="WHERE combines tables",
            expected_answer="WHERE filters rows",
            explanation="WHERE is for filtering, JOIN is for combining.",
            target_bloom_level=2
        ))
        
        # Check assertions
        self.assertTrue(result["success"])
        self.assertAlmostEqual(result["score"], 0.85) # 8.5 / 10
        
        # Verify Prompt contains key JudgeLM phrases
        call_args = self.mock_llm.acomplete.call_args[0][0]
        self.assertIn("[The Start of Assistant 1's Answer]", call_args)
        self.assertIn("receives a score of 10", call_args)
        self.assertIn("[Rubric]", call_args)
        
        loop.close()

    def test_score_judgelm_fallback_json(self):
        """Verify JSON fallback if top line is missing"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Mock LLM Response (JSON Only)
        self.mock_llm.acomplete = AsyncMock(return_value=MagicMock(text="""
I analyzed the answer.
```json
{
    "correctness": 5,
    "completeness": 5,
    "clarity": 5
}
```
"""))

        result = loop.run_until_complete(self.agent._score_response(
            learner_response="bad answer",
            expected_answer="good answer",
            explanation="reason",
            target_bloom_level=2
        ))
        
        self.assertTrue(result["success"])
        # Calculation: (5*0.6 + 5*0.2 + 5*0.2) / 10 = 5/10 = 0.5
        self.assertAlmostEqual(result["score"], 0.5)
        
        loop.close()

if __name__ == "__main__":
    unittest.main()
