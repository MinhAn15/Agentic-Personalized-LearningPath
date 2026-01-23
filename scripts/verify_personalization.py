"""
Verify Personalization Sensitivity (The "Identity" Check)
Runs the same question through the TutorAgent for two distinct learner profiles
to demonstrate adaptive pedagogical strategies.

Scenario:
- Question: "Explain the concept of SQL IOINS"
- Profile A: Alice (Beginner, Visual, Impatient) -> Expects Analogies, Diagrams, Brevity
- Profile B: David (Expert, Textual, Detail-oriented) -> Expects Technical Definitions, Performance metrics
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agents.tutor_agent import TutorAgent
from backend.models.schemas import LearnerProfile
from backend.models.enums import SkillLevel, LearningStyle
# from backend.core.state_manager import StateManager # REMOVED
# from backend.core.event_bus import MockEventBus # REMOVED

class MockEventBus:
    def subscribe(self, event, handler):
        pass
    
    async def publish(self, sender, receiver, type, payload):
        print(f"[EventBus] {sender} -> {receiver}: {type}")

class MockRedisClient:
    def __init__(self):
        self.data = {}
    async def get(self, key): return self.data.get(key)
    async def set(self, key, value, ttl=None): self.data[key] = value
    async def delete(self, key): self.data.pop(key, None)

class MockStateManager:
    def __init__(self):
        self.profiles = {}
        self.redis = MockRedisClient()
    
    async def get_learner_profile(self, learner_id):
        return self.profiles.get(learner_id)
        
    async def get(self, key):
        # Allow agents to get profile via key
        if key.startswith("profile:"):
            lid = key.split(":")[1]
            return self.profiles.get(lid)
        return None

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("VerifyPersonalization")

async def run_comparison():
    print("="*60)
    print("PERSONALIZATION SENSITIVITY CHECK")
    print("="*60)
    
    # Setup Infrastructure
    state_manager = MockStateManager()
    event_bus = MockEventBus()
    agent = TutorAgent("tutor_verify", state_manager, event_bus)
    
    # Define Profiles
    profile_a = LearnerProfile(
        learner_id="alice_visual",
        name="Alice (Beginner/Visual)",
        skill_level=SkillLevel.BEGINNER,
        learning_style=LearningStyle.VISUAL,
        preferences={"verbosity": "low", "analogy_frequency": "high"},
        learning_goal=["SQL_BASICS"],
        goal="Learn SQL basics",
        current_mastery=[]
    )
    
    profile_b = LearnerProfile(
        learner_id="david_expert",
        name="David (Expert/Textual)",
        skill_level=SkillLevel.ADVANCED,
        learning_style=LearningStyle.READING,
        preferences={"verbosity": "high", "technical_depth": "deep"},
        learning_goal=["SQL_OPTIMIZATION"],
        goal="Master query optimization",
        current_mastery=[]
    )
    
    # Store profiles in state (Tutor retrieves them via state_manager usually, 
    # but here we pass profile attributes explicitly via simulation if needed, 
    # or ensure state_manager has them)
    state_manager.profiles[profile_a.learner_id] = profile_a
    state_manager.profiles[profile_b.learner_id] = profile_b
    
    question = "Explain SQL JOINs to me."
    concept_id = "concept_sql_joins" # Simulated context
    
    # Run for Alice
    print(f"\nTESTING PROFILE A: {profile_a.name}")
    print(f"   Style: {profile_a.learning_style.value}, Level: {profile_a.skill_level.value}")
    print("-" * 50)
    
    response_a = await agent.execute(
        learner_id=profile_a.learner_id,
        question=question,
        concept_id=concept_id,
        force_real=True # Use Real LLM for actual variation
    )
    print(f"\nRESPONSE A:\n{response_a.get('guidance')}")
    
    # Run for David
    print(f"\n\nTESTING PROFILE B: {profile_b.name}")
    print(f"   Style: {profile_b.learning_style.value}, Level: {profile_b.skill_level.value}")
    print("-" * 50)
    
    response_b = await agent.execute(
        learner_id=profile_b.learner_id,
        question=question,
        concept_id=concept_id,
        force_real=True
    )
    print(f"\nRESPONSE B:\n{response_b.get('guidance')}")
    
    # Simple Analysis
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)
    len_a = len(response_a.get('guidance', ''))
    len_b = len(response_b.get('guidance', ''))
    
    print(f"Length Variance: Alice ({len_a} chars) vs David ({len_b} chars)")
    if len_b > len_a * 1.2:
        print("PASS: Expert response is significantly more detailed.")
    elif len_a > len_b:
         print("NOTE: Beginner response longer (maybe due to analogies?).")
    else:
         print("NOTE: Similar lengths.")
         
    # Check key differentiators
    v_keywords = ["visualize", "diagram", "imagine", "picture", "like a"]
    t_keywords = ["set theory", "cartesian", "performance", "optimization", "relational algebra"]
    
    found_v = [w for w in v_keywords if w in response_a.get('guidance', '').lower()]
    found_t = [w for w in t_keywords if w in response_b.get('guidance', '').lower()]
    
    print(f"Alice Visual Keywords Found: {found_v}")
    print(f"David Technical Keywords Found: {found_t}")

if __name__ == "__main__":
    asyncio.run(run_comparison())
