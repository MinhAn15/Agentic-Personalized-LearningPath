import unittest
import asyncio
import sys
import os

# Add project root to sys.path to allow running as script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any, List

# Mock external dependencies BEFORE importing agents that use them
sys.modules['llama_index'] = MagicMock()
sys.modules['llama_index.core'] = MagicMock()
sys.modules['llama_index.llms'] = MagicMock()
sys.modules['llama_index.llms.gemini'] = MagicMock()
sys.modules['llama_index.embeddings'] = MagicMock()
sys.modules['llama_index.embeddings.gemini'] = MagicMock()

from backend.core.event_bus import EventBus
from backend.core.state_manager import CentralStateManager
from backend.models.dialogue import UserIntent
from backend.models.evaluation import ErrorType, PathDecision
from backend.agents.knowledge_extraction_agent import KnowledgeExtractionAgent, RelationshipType
from backend.agents.profiler_agent import ProfilerAgent, DiagnosticState
from backend.agents.path_planner_agent import PathPlannerAgent, ChainingMode
from backend.agents.tutor_agent import TutorAgent, SocraticState
from backend.agents.evaluator_agent import EvaluatorAgent
from backend.agents.kag_agent import KAGAgent

class TestEndToEndFlow(unittest.IsolatedAsyncioTestCase):
    """
    End-to-End Integration Test for the Agentic Personalized Learning Path.
    Scenario: "The Python Beginner's Journey"
    """

    async def asyncSetUp(self):
        # 1. Shared Infrastructure
        self.event_bus = EventBus()
        self.state_manager = MagicMock(spec=CentralStateManager)
        self.state_manager.get_learner_profile = AsyncMock(return_value={
            "learner_id": "learner_001",
            "name": "Test Learner",
            "goal": "Learn Python for Data Science",
            "topic": "Python",
            "time_available": 30,
            "learning_style": "VISUAL",
            "skill_level": "BEGINNER",
            "mastery_map": {"concept_var": 0.1, "concept_dtype": 0.0}
        })
        self.state_manager.update_learner_progress = AsyncMock(return_value=True)
        self.state_manager.set = AsyncMock(return_value=True)
        self.state_manager.get = AsyncMock(return_value=None)
        self.state_manager.get_state = AsyncMock(return_value={
            "learner_id": "learner_001",
            "name": "Test Learner",
            "goal": "Learn Python for Data Science",
            "topic": "Python"
        })
        self.state_manager.neo4j = MagicMock()
        self.state_manager.neo4j.run_query = AsyncMock(return_value=[
            {"concept_id": "concept_var", "name": "Variables", "difficulty": 1},
            {"concept_id": "concept_dtype", "name": "Data Types", "difficulty": 2}
        ])
        # Add redis and postgres mocks
        self.state_manager.redis = MagicMock()  # Use MagicMock for sync methods
        mock_pipeline = MagicMock()
        mock_pipeline.get = MagicMock(return_value=mock_pipeline)  # Chainable
        mock_pipeline.execute = AsyncMock(return_value=[None, None])  # Return empty results
        self.state_manager.redis.pipeline = MagicMock(return_value=mock_pipeline)
        self.state_manager.redis.set = AsyncMock(return_value=True)
        self.state_manager.redis.get = AsyncMock(return_value=None)
        self.state_manager.redis.setex = AsyncMock(return_value=True)
        self.state_manager.postgres = AsyncMock()
        self.state_manager.postgres.save_learner = AsyncMock(return_value=True)
        self.state_manager.postgres.get_learner = AsyncMock(return_value=None)
        
        # Mocks for databases
        self.mock_course_kg = AsyncMock()
        self.mock_personal_kg = AsyncMock()
        self.mock_redis = AsyncMock()
        
        # Mocks for LLM
        self.mock_llm = MagicMock()
        self.mock_embedding = MagicMock()
        # Default embedding vector (dimension 768)
        self.mock_embedding.get_text_embedding.return_value = [0.1] * 768

        # 2. Instantiate Agents with Mocks
        # Agent 1: Knowledge Extraction
        self.agent1 = KnowledgeExtractionAgent(
            "agent1", self.state_manager, self.event_bus, llm=self.mock_llm
        )
        # Mock internal helpers for Agent 1 to bypass real Neo4j/Gemini
        self.agent1._get_batch_upserter = MagicMock()
        self.agent1._get_provenance_manager = MagicMock()

        # Agent 2: Profiler
        self.agent2 = ProfilerAgent(
            "agent2", self.state_manager, self.event_bus, llm=self.mock_llm
        )
        self.agent2.personal_kg = self.mock_personal_kg
        self.agent2.redis = self.mock_redis

        # Agent 3: Path Planner
        self.agent3 = PathPlannerAgent(
            "agent3", self.state_manager, self.event_bus, llm=self.mock_llm
        )
        self.agent3.course_kg = self.mock_course_kg
        self.agent3.personal_kg = self.mock_personal_kg
        self.agent3.redis = self.mock_redis

        # Agent 4: Tutor
        self.agent4 = TutorAgent(
            "agent4", self.state_manager, self.event_bus, llm=self.mock_llm
        )
        self.agent4.course_kg = self.mock_course_kg
        self.agent4.personal_kg = self.mock_personal_kg
        # Mock vector store loading
        self.agent4._load_vector_index = MagicMock() # Don't load real index

        # Agent 5: Evaluator
        self.agent5 = EvaluatorAgent(
            "agent5", self.state_manager, self.event_bus, llm=self.mock_llm
        )
        # Mock scoring to be deterministic for passing
        self.agent5._score_response = AsyncMock(return_value=0.9) 
        self.agent5._classify_error = AsyncMock(return_value=ErrorType.CORRECT)

        # Agent 6: KAG
        self.agent6 = KAGAgent(
            "agent6", self.state_manager, self.event_bus, llm=self.mock_llm
        )
        self.agent6.personal_kg = self.mock_personal_kg
        self.agent6.kg_synchronizer = AsyncMock() # Mock the sync logic
        self.agent6.note_generator = AsyncMock() # Mock generation

        # Register agents (if needed by your architecture, mainly via event bus)
        # In this test, we call execute directly or simulate events.

    async def test_python_beginners_journey(self):
        print("\n--- Starting End-to-End Test: Python Beginner's Journey ---")
        
        learner_id = "learner_001"
        
        # --- Step 1: Ingestion (Agent 1) ---
        print("[Step 1] Ingestion (Agent 1)")
        # Pre-condition: We assume content is ingested. 
        # We simulate a "Concepts Ready" state by mocking Course KG returns.
        self.mock_course_kg.query.return_value = [
            {"c": {"id": "concept_var", "name": "Variables", "difficulty": 1}},
            {"c": {"id": "concept_dtype", "name": "Data Types", "difficulty": 2}}
        ]
        
        # --- Step 2: Profiling (Agent 2) ---
        print("[Step 2] Profiling (Agent 2)")
        # User goal: "I want to learn Python for Data Science"
        # Mock LLM response for goal parsing
        # User goal: "I want to learn Python for Data Science"
        # Mock LLM response for goal parsing
        # Note: Agents use 'acomplete', so we must mock that.
        self.mock_llm.acomplete = AsyncMock(side_effect=[
            # Agent 2: Goal Parsing
            MagicMock(text='{"topic": "Python", "purpose": "Data Science", "goal": "Learn Python for Data Science", "current_level": "Beginner", "time_available": 30}'),
            # Agent 2: Diagnostic Questions
            MagicMock(text='["What is a variable?", "List basic data types"]'),
             # Agent 2: Diagnostic Assessment (Simulated result)
            MagicMock(text='{"mastery": 0.1, "learning_style": "Visual"}'),
             # Agent 3: Path Planning Recommendation (later)
            MagicMock(text='["concept_var"]'),
             # Agent 4: Intent Classification
            MagicMock(text='SENSE_MAKING'),
             # Agent 4: Socratic Response
            MagicMock(text='Think of a variable as a container...'),
             # Agent 5: Feedback (Mocked in setup but let's be safe)
            MagicMock(text='Great job!'),
             # Agent 6: Note Content
            MagicMock(text='{"key_insight": "Variables store data", "personal_example": "Like a box"}'),
        ])

        # Execute Agent 2
        profiler_response = await self.agent2.execute(
            learner_id=learner_id,
            learner_message="I want to learn Python for Data Science"
        )
        
        self.assertIn("profile", profiler_response)
        self.assertEqual(profiler_response["profile"]["topic"], "Python")
        print(f"  > Profile Created: topic={profiler_response['profile']['topic']}, goal={profiler_response['profile']['goal']}")

        # --- Step 3: Planning (Agent 3) ---
        print("[Step 3] Planning (Agent 3)")
        # Mock Course KG structure for planner
        # Variables -> NEXT -> Data Types
        self.agent3._build_relationship_map = MagicMock(return_value={
            "concept_var": {"NEXT": ["concept_dtype"]},
            "concept_dtype": {}
        })
        self.agent3._get_chain_candidates = MagicMock(return_value=["concept_var"]) # Deterministic return

        # Execute Agent 3
        path_response = await self.agent3.execute(
            learner_id=learner_id,
            learner_profile=profiler_response["profile"]
        )
        
        self.assertIn("learning_path", path_response)
        first_concept = path_response["learning_path"][0]
        self.assertEqual(first_concept["concept"], "concept_var")
        print(f"  > Path Planned: Start with {first_concept['concept']}")

        # Simulate Event: PATH_PLANNED
        await self.event_bus.publish(
            sender="agent3",
            receiver="agent4",
            message_type="PATH_PLANNED",
            payload={
                "learner_id": learner_id,
                "path": path_response["learning_path"]
            }
        )

        # --- Step 4: Tutoring (Agent 4) ---
        print("[Step 4] Tutoring (Agent 4)")
        # User asks: "What is a variable?"
        # Mock TutorAgent internal methods for success path
        self.agent4._get_concept_from_kg = AsyncMock(return_value={
            "concept_id": "concept_var", "name": "Variables", "content": "Variables are containers for storing data values.",
            "difficulty": 1, "prerequisites": []
        })
        self.agent4._get_learner_state = AsyncMock(return_value={
            "mastery": 0.1, "hint_level": 0, "conversation_turns": 0
        })
        self.agent4._three_layer_grounding = AsyncMock(return_value={
            "success": True,
            "confidence": 0.9,
            "sources": ["RAG", "CourseKG"],
            "context": {"rag": "A variable is a named location in memory...", "kg": "Variables store values"}
        })
        self.agent4._classify_intent = AsyncMock(return_value=UserIntent.SENSE_MAKING)
        self.agent4._generate_socratic_response = AsyncMock(return_value={
            "success": True,
            "guidance": "Think of a variable like a labeled box...",
            "follow_up_question": "What kind of data might you store in a variable?"
        })
        
        # Execute Agent 4
        tutor_response = await self.agent4.execute(
            learner_id=learner_id,
            question="What is a variable?",
            concept_id="concept_var"
        )
        
        self.assertEqual(tutor_response["socratic_state"], SocraticState.PROBING.value)  # Initial state
        print(f"  > Tutor Response ({tutor_response['socratic_state']}): {tutor_response['guidance'][:50]}...")

        # --- Step 5: Evaluation (Agent 5) ---
        print("[Step 5] Evaluation (Agent 5)")
        # User answers correctly
        user_answer = "It is a named storage for values."
        
        # Mock EvaluatorAgent internal methods for success path
        self.agent5._score_response = AsyncMock(return_value={"score": 0.95, "confidence": 0.9})
        self.agent5._classify_error = AsyncMock(return_value=ErrorType.CORRECT)
        self.agent5._detect_misconception = AsyncMock(return_value=None)
        self.agent5._generate_feedback = AsyncMock(return_value="Excellent! Your understanding is correct.")
        self.agent5._make_path_decision = AsyncMock(return_value=PathDecision.MASTERED)
        self.agent5._update_learner_mastery = AsyncMock(return_value=0.95)
        
        # Execute Agent 5
        eval_response = await self.agent5.execute(
            learner_id=learner_id,
            concept_id="concept_var",
            learner_response=user_answer,
            expected_answer="Storage for data",
            explanation="Concept definition"
        )
        
        self.assertGreaterEqual(eval_response["score"], 0.9)
        self.assertEqual(eval_response["decision"], "MASTERED") # As per mock score 0.9
        print(f"  > Evaluation: Score={eval_response['score']}, Decision={eval_response['decision']}")

        # Simulate Event: EVALUATION_COMPLETED
        # This triggers Agent 3 (Adaptation) and Agent 6 (Artifact)
        event_payload = {
            "learner_id": learner_id,
            "concept_id": "concept_var",
            "score": 0.9,
            "decision": "MASTERED",
            "error_type": "CORRECT",
            "misconceptions": [],
            "timestamp": "2024-01-01T00:00:00"
        }
        await self.event_bus.publish(
            sender="agent5",
            receiver="agent3",
            message_type="EVALUATION_COMPLETED",
            payload=event_payload
        )
        
        # --- Step 6: Adaptation (Agent 3 - Triggered via Event) ---
        print("[Step 6] Adaptation (Check Agent 3 Logic)")
        # In a real app, Agent 3 listens to event. Here we manually check the logic 
        # that would run inside _on_evaluation_feedback
        
        # Mock Redis get for MAB stats to verify update
        # We expect Agent 3 to update Q-value for concept_var.
        # But since we mocked Redis, we just verify the call logic if we were testing internal methods.
        # Instead, let's verify Agent 3's decision logic for the NEXT execute call involves "ACCELERATE" (Flow)
        # or unlocking the next concept.
        
        self.agent3._select_chain_mode = MagicMock(return_value=ChainingMode.ACCELERATE)
        self.agent3._get_chain_candidates = MagicMock(return_value=["concept_dtype"]) # Next concept
        
        # Execute Agent 3 again to get next step
        next_step_response = await self.agent3.execute(
            learner_id=learner_id,
            learner_profile=profiler_response["profile"] # In reality profile is updated
        )
        
        next_concept = next_step_response["learning_path"][0]
        self.assertEqual(next_concept["concept"], "concept_dtype")
        print(f"  > Adaptive Path: Advanced to {next_concept['concept']} (Mode: ACCELERATE)")

        # --- Step 7: Artifact Generation (Agent 6 - Triggered via Event) ---
        print("[Step 7] Artifact Generation (Agent 6)")
        # We need to manually invoke the handler or ensure the event bus delivered it.
        # Since we are using a real EventBus, if Agent 6 subscribed, it should receive it.
        # However, BaseAgent doesn't auto-subscribe in init unless we explicitly call a method or run loop.
        # Let's manually trigger the handler to be sure for this unit test.
        
        # Mock Note Generator return
        self.agent6.note_generator.generate_note.return_value = {
            "note_id": "note_123",
            "type": "ATOMIC",
            "content": "Variables store...",
            "concept_id": "concept_var"
        }
        self.agent6.kg_synchronizer.sync_note_to_kg.return_value = True
        
        await self.agent6._on_evaluation_completed(event_payload)
        
        # Verify Generator called
        self.agent6.note_generator.generate_note.assert_awaited_once()
        # Verify Sync called
        self.agent6.kg_synchronizer.sync_note_to_kg.assert_awaited_once()
        print("  > Zettelkasten Note Generated & Synced to Personal KG")

        print("--- Test Complete: Success ---")

if __name__ == "__main__":
    unittest.main()
