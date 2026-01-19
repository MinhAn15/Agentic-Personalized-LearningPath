import asyncio
import logging
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.evaluator_agent import EvaluatorAgent
from backend.models.evaluation import PathDecision

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EvaluatorDemo")

# Mock Dependencies
class MockEventBus:
    def subscribe(self, topic, handler): pass
    async def publish(self, topic=None, payload=None, **kwargs): 
        logger.info(f"EVENT PUBLISHED: {topic} (Payload: {payload}, Kwargs: {kwargs})")

class MockNeo4j:
    async def run_query(self, query, **kwargs):
        if "CourseConcept" in query:
            return [{"c": {
                "name": "SQL_JOINS", 
                "description": "Combines rows from two or more tables",
                "difficulty": 3,
                "common_misconceptions": ["Thinking JOIN is same as UNION", "Forgetting ON clause"]
            }}]
        # Determine LKT update or other queries
        return []

class MockStateManager:
    def __init__(self):
        self.neo4j = MockNeo4j()
        self.data_store = {}
        
    async def get_learner_profile(self, learner_id):
        return {
            "learner_id": learner_id, 
            "current_mastery": [], 
            "interaction_history": []
        }
    
    async def set(self, key, value):
        self.data_store[key] = value
        
    async def get(self, key):
        return self.data_store.get(key)
        
    @property
    def redis(self):
        return self

async def run_demo():
    print("\n🚀 STARTING REAL EVALUATOR (JudgeLM) DEMO\n" + "="*50)
    
    agent = EvaluatorAgent("evaluator-demo", MockStateManager(), MockEventBus())
    
    # CASE: Semi-Correct Answer (To test Feedback generation)
    learner_id = "demo_learner_01"
    concept_id = "SQL_JOINS"
    # Learner gives a vague answer (Not fully wrong, but not complete)
    learner_response = "JOIN is used to combine two tables together."  
    expected_answer = "JOIN combines rows from two or more tables based on a related column between them."
    explanation = "JOIN requires a join condition (ON) to match rows, otherwise it's a Cartesian product."
    
    print(f"Concept: {concept_id}")
    print(f"Learner Response: '{learner_response}'")
    print(f"Expected Answer:  '{expected_answer}'")
    print("-" * 50)
    
    print("\n🧠 EXECUTE: Calling EvaluatorAgent with force_real=True...")
    
    # Override LLM settings inside the agent to ensure we don't hit other mock guards if any
    # (Though force_real should handle it)
    
    result = await agent.execute(
        learner_id=learner_id,
        concept_id=concept_id,
        learner_response=learner_response,
        expected_answer=expected_answer,
        correct_answer_explanation=explanation,
        force_real=True # <--- CRITICAL
    )
    
    print("\n✅ RESULT RECEIVED:")
    print("-" * 20)
    print(f"Success: {result['success']}")
    print(f"Score: {result.get('score')}  (Expected < 0.9 for vague answer)")
    print(f"Error Type: {result.get('error_type')}")
    print(f"Decision: {result.get('decision')}")
    print(f"Misconception: {result.get('misconception')}")
    print(f"Feedback:\n> {result.get('feedback')}")
    
    if "Mock" in str(result.get('feedback')):
         print("\n❌ FAILURE: Output contains 'Mock'!")
    else:
         print("\n✅ SUCCESS: JudgeLM logic executed.")

if __name__ == "__main__":
    asyncio.run(run_demo())
