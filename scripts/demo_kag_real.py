import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.kag_agent import KAGAgent
from backend.models.schemas import KAGInput

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("kag-demo")

# Mock Dependencies
class MockEventBus:
    def subscribe(self, topic, handler): pass
    async def publish(self, topic=None, payload=None, **kwargs): 
        logger.info(f"EVENT PUBLISHED: {topic} (Payload: {payload})")

class MockNeo4j:
    async def run_query(self, query, **kwargs):
        logger.info(f"NEO4J QUERY: {query[:50]}... Params: {kwargs}")
        return []

class MockStateManager:
    def __init__(self):
        self.neo4j = MockNeo4j()
    
    async def set(self, key, value): pass
    
    @property
    def redis(self): return self

async def run_demo():
    print("\n🚀 STARTING REAL KAG (MemGPT) DEMO\n" + "="*50)
    
    # 1. Initialize Agent
    event_bus = MockEventBus()
    state_manager = MockStateManager()
    agent = KAGAgent("kag-demo", state_manager, event_bus)
    
    # 2. Test Data (Simulate a Tutor Session Conclusion)
    learner_id = "demo_learner_01"
    concept_id = "SQL_JOINS"
    session_data = {
        "question": "What is the difference between INNER JOIN and LEFT JOIN?",
        "answer": "INNER JOIN returns only matching rows, while LEFT JOIN returns all rows from the left table and matches from the right.",
        "score": 0.95,
        "feedback": "Correct! You clearly understand the distinction.",
        "source_context": "Tutor Session #123"
    }
    
    print(f"Concept: {concept_id}")
    print(f"Learner Answer: {session_data['answer']}")
    print("-" * 50)
    
    # 3. Execute Real Zettelkasten Generation
    print("\n🧠 EXECUTE: Calling KAGAgent with force_real=True (Generate Artifact)...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await agent.execute(
                action="generate_artifact",
                learner_id=learner_id,
                concept_id=concept_id,
                session_data=session_data,
                force_real=True  # ACTIVATING REAL LLM
            )
            
            if result["success"]:
                print("\n✅ RESULT RECEIVED:")
                print("-" * 20)
                print(f"Note ID: {result['note_id']}")
                print(f"Type: {result['artifact_type']}")
                print(f"Preview: {result['content_preview']}")
                print(f"Tags: {result['tags']}")
                print("\n✅ SUCCESS: Zettelkasten logic executed.")
                break
            else:
                error_msg = str(result.get('error', ''))
                print(f"\n❌ FAILED: {error_msg}")
                
                if "429" in error_msg or "quota" in error_msg.lower():
                    print(f"⚠️ Quota exceeded (Attempt {attempt+1}/{max_retries}). Retrying in 20s...")
                    await asyncio.sleep(20)
                    continue
                else:
                    break
                
        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Quota exceeded (Attempt {attempt+1}/{max_retries}). Retrying in 20s...")
                await asyncio.sleep(20)
            else:
                logger.error(f"Error executing KAG agent: {e}")
                import traceback
                traceback.print_exc()
                break

if __name__ == "__main__":
    asyncio.run(run_demo())
