"""
Experiment Runner for Full-Scale Experiments
Orchestrates the 6-agent pipeline and collects metrics.

Usage:
    python scripts/run_experiment.py                    # Run with mock LLM
    python scripts/run_experiment.py --real             # Run with real LLM (uses API quota)
    python scripts/run_experiment.py --learner alice    # Run for specific learner
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_settings
from backend.models.schemas import (
    DocumentInput, LearnerProfile, TutorInput, EvaluationInput
)
from backend.models.enums import DocumentType
from backend.agents.baseline_agent import BaselineAgent

# =============================================
# CONFIGURATION
# =============================================

DATA_DIR = Path(__file__).parent.parent / "data" / "experiments"
RESULTS_DIR = DATA_DIR / "results"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ExperimentRunner")


# =============================================
# MOCK DATABASE DRIVERS
# =============================================

class MockNeo4jDriver:
    """Mock Neo4j driver for experiment execution."""
    
    async def run_query(self, query: str, **kwargs):
        """Return mock query results."""
        return []
    
    def run_query_sync(self, query: str, **kwargs):
        """Synchronous version."""
        return []
    
    async def execute_query(self, query: str, **kwargs):
        """Execute query and return mock results."""
        return {"records": [], "summary": {}}


class MockPostgresDriver:
    """Mock Postgres driver for experiment execution."""
    
    def __init__(self):
        self._learners: Dict[str, Any] = {}
    
    async def execute(self, query: str, *args):
        """Execute query."""
        return None
    
    async def fetch(self, query: str, *args):
        """Fetch results."""
        return []
    
    async def fetchrow(self, query: str, *args):
        """Fetch single row."""
        return None
    
    async def create_learner(self, learner_id: str, name: str = "", **kwargs):
        """Create a learner record."""
        self._learners[learner_id] = {"learner_id": learner_id, "name": name, **kwargs}
        return self._learners[learner_id]
    
    async def get_learner(self, learner_id: str):
        """Get a learner record."""
        return self._learners.get(learner_id)
    
    async def update_learner(self, learner_id: str, **kwargs):
        """Update a learner record."""
        if learner_id in self._learners:
            self._learners[learner_id].update(kwargs)
        return self._learners.get(learner_id)


class MockRedisClient:
    """Mock Redis client for experiment execution."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
    
    async def get(self, key: str):
        return self._data.get(key)
    
    async def set(self, key: str, value: Any, **kwargs):
        self._data[key] = value
    
    async def delete(self, key: str):
        self._data.pop(key, None)
    
    async def acquire_lock(self, key: str, **kwargs):
        return True
    
    async def release_lock(self, key: str):
        pass


# =============================================
# MOCK STATE MANAGER & EVENT BUS
# =============================================

class MockStateManager:
    """Enhanced state manager with all required database mocks."""
    
    def __init__(self):
        self.profiles: Dict[str, LearnerProfile] = {}
        self.neo4j = MockNeo4jDriver()
        self.postgres = MockPostgresDriver()
        self.redis = MockRedisClient()
    
    async def get_learner_profile(self, learner_id: str) -> Optional[LearnerProfile]:
        return self.profiles.get(learner_id)
    
    async def save_learner_profile(self, profile: LearnerProfile):
        self.profiles[profile.learner_id] = profile
    
    async def get_profile_dict(self, learner_id: str) -> Optional[Dict]:
        """Return profile as dict for agents that expect dict format."""
        profile = self.profiles.get(learner_id)
        if profile:
            return profile.model_dump()
        return None
    
    async def set(self, key: str, value: Any):
        """Set state value (delegate to redis)."""
        await self.redis.set(key, value)
        
    async def get(self, key: str):
        """Get state value (delegate to redis)."""
        return await self.redis.get(key)


class MockEventBus:
    """Minimal event bus for experiment execution."""
    
    def __init__(self):
        self.events: List[Dict] = []
    
    def subscribe(self, topic: str, handler):
        pass
    
    async def publish(self, topic: str = None, payload: Dict = None, **kwargs):
        """Mock publish accepting flexible arguments."""
        event = {
            "topic": topic,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.events.append(event)


# =============================================
# METRICS COLLECTOR
# =============================================

class MetricsCollector:
    """Collects and aggregates experiment metrics."""
    
    def __init__(self):
        self.agent_calls: Dict[str, List[Dict]] = {
            "knowledge_extraction": [],
            "profiler": [],
            "path_planner": [],
            "tutor": [],
            "evaluator": [],
            "kag": [],
        }
        self.start_time = time.time()
    
    def record_call(self, agent_name: str, latency_ms: float, success: bool, metadata: Dict = None):
        self.agent_calls[agent_name].append({
            "latency_ms": latency_ms,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        })
    
    def get_summary(self) -> Dict:
        total_time = time.time() - self.start_time
        
        summary = {
            "experiment_duration_seconds": total_time,
            "agents": {},
        }
        
        for agent_name, calls in self.agent_calls.items():
            if calls:
                latencies = [c["latency_ms"] for c in calls]
                successes = [c["success"] for c in calls]
                summary["agents"][agent_name] = {
                    "total_calls": len(calls),
                    "success_rate": sum(successes) / len(successes) if successes else 0,
                    "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
                    "min_latency_ms": min(latencies) if latencies else 0,
                    "max_latency_ms": max(latencies) if latencies else 0,
                }
        
        return summary


# =============================================
# EXPERIMENT RUNNER
# =============================================

class ExperimentRunner:
    """Orchestrates the full experiment pipeline."""
    
    def __init__(self, use_real_llm: bool = False, learner_filter: str = None, use_baseline: bool = False):
        self.use_real_llm = use_real_llm
        self.use_baseline = use_baseline
        self.learner_filter = learner_filter
        self.state_manager = MockStateManager()
        self.event_bus = MockEventBus()
        self.metrics = MetricsCollector()
        self.results = {
            "experiment_id": str(uuid.uuid4()),
            "started_at": datetime.now().isoformat(),
            "config": {
                "use_real_llm": use_real_llm,
                "learner_filter": learner_filter,
                "use_baseline": use_baseline,
            },
            "phases": {},
        }
    
    def load_experiment_config(self) -> Dict:
        """Load experiment configuration."""
        config_path = DATA_DIR / "experiment_config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def load_learner_profiles(self) -> List[LearnerProfile]:
        """Load learner profiles from JSON files."""
        profiles_dir = DATA_DIR / "learner_profiles"
        profiles = []
        
        for profile_file in profiles_dir.glob("*.json"):
            if self.learner_filter and self.learner_filter not in profile_file.stem:
                continue
            
            with open(profile_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert back to LearnerProfile
                profile = LearnerProfile(**data)
                profiles.append(profile)
                self.state_manager.profiles[profile.learner_id] = profile
        
        return profiles
    
    def load_course_materials(self) -> List[Dict]:
        """Load course materials from markdown files."""
        pdfs_dir = DATA_DIR / "pdfs"
        materials = []
        
        for md_file in sorted(pdfs_dir.glob("*.md")):
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                materials.append({
                    "filename": md_file.name,
                    "content": content,
                    "title": md_file.stem.replace("_", " ").title(),
                })
        
        return materials
    
    async def run_phase_1_knowledge_extraction(self, materials: List[Dict]) -> Dict:
        """Phase 1: Extract knowledge from course materials."""
        logger.info("=" * 60)
        logger.info("Phase 1: Knowledge Extraction")
        logger.info("=" * 60)
        
        from backend.agents.knowledge_extraction_agent import KnowledgeExtractionAgent
        
        agent = KnowledgeExtractionAgent(
            agent_id="exp_ke_agent",
            state_manager=self.state_manager,
            event_bus=self.event_bus
        )
        
        extracted = []
        for material in materials:
            logger.info(f"Processing: {material['filename']}")
            
            start_time = time.time()
            try:
                result = await agent.execute(
                    document=DocumentInput(
                        content=material["content"],
                        title=material["title"],
                        document_type=DocumentType.LECTURE,
                        force_real=self.use_real_llm
                    )
                )
                
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record_call("knowledge_extraction", latency_ms, True, {
                    "filename": material["filename"],
                    "concepts_count": result.get("total_concepts", 0) if isinstance(result, dict) else 0,
                })
                
                extracted.append({
                    "filename": material["filename"],
                    "result": result if isinstance(result, dict) else {"raw": str(result)},
                })
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record_call("knowledge_extraction", latency_ms, False, {"error": str(e)})
                logger.error(f"Error processing {material['filename']}: {e}")
                extracted.append({"filename": material["filename"], "error": str(e)})
        
        return {"extracted_count": len(extracted), "items": extracted}
    
    async def run_phase_2_profiling(self, profiles: List[LearnerProfile]) -> Dict:
        """Phase 2: Profile learners."""
        logger.info("=" * 60)
        logger.info("Phase 2: Learner Profiling")
        logger.info("=" * 60)
        
        from backend.agents.profiler_agent import ProfilerAgent
        
        agent = ProfilerAgent(
            agent_id="exp_profiler",
            state_manager=self.state_manager,
            event_bus=self.event_bus
        )
        
        profiled = []
        for profile in profiles:
            logger.info(f"Profiling: {profile.name}")
            
            start_time = time.time()
            try:
                # Simulate profiling by updating mastery
                result = await agent.execute(
                    learner_id=profile.learner_id,
                    learner_message=f"I want to learn {profile.goal or 'Python'}",
                    force_real=self.use_real_llm
                )
                
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record_call("profiler", latency_ms, True, {
                    "learner_name": profile.name,
                    "skill_level": str(profile.skill_level),
                })
                
                profiled.append({
                    "learner_id": profile.learner_id,
                    "name": profile.name,
                    "result": result if isinstance(result, dict) else {"raw": str(result)},
                })
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record_call("profiler", latency_ms, False, {"error": str(e)})
                logger.error(f"Error profiling {profile.name}: {e}")
                profiled.append({"learner_id": profile.learner_id, "error": str(e)})
        
        return {"profiled_count": len(profiled), "items": profiled}
    
    async def run_phase_3_path_planning(self, profiles: List[LearnerProfile]) -> Dict:
        """Phase 3: Generate learning paths."""
        logger.info("=" * 60)
        logger.info("Phase 3: Path Planning (ToT)")
        logger.info("=" * 60)
        
        from backend.agents.path_planner_agent import PathPlannerAgent
        
        agent = PathPlannerAgent(
            agent_id="exp_planner",
            state_manager=self.state_manager,
            event_bus=self.event_bus
        )
        
        paths = []
        for profile in profiles:
            logger.info(f"Planning path for: {profile.name}")
            
            start_time = time.time()
            try:
                result = await agent.execute(
                    learner_id=profile.learner_id,
                    force_real=self.use_real_llm
                )
                
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record_call("path_planner", latency_ms, True, {
                    "learner_name": profile.name,
                })
                
                paths.append({
                    "learner_id": profile.learner_id,
                    "name": profile.name,
                    "result": result if isinstance(result, dict) else {"raw": str(result)},
                })
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record_call("path_planner", latency_ms, False, {"error": str(e)})
                logger.error(f"Error planning for {profile.name}: {e}")
                paths.append({"learner_id": profile.learner_id, "error": str(e)})
        
        return {"paths_count": len(paths), "items": paths}
    
    async def run_phase_4_tutoring(self, profiles: List[LearnerProfile], sessions_per_learner: int = 3) -> Dict:
        """Phase 4: Run tutoring sessions."""
        logger.info("=" * 60)
        logger.info("Phase 4: Tutoring (CoT)")
        logger.info("=" * 60)
        
        from backend.agents.tutor_agent import TutorAgent
        
        if self.use_baseline:
            logger.info("Using Baseline Agent (Vanilla RAG)")
            agent = BaselineAgent(agent_id="exp_baseline_tutor")
        else:
            agent = TutorAgent(
                agent_id="exp_tutor",
                state_manager=self.state_manager,
                event_bus=self.event_bus
            )
        
        sessions = []
        
        for profile in profiles:
            # 1. Get generated path for this learner
            path_results = self.results.get("phases", {}).get("3_path_planning", {}).get("items", [])
            learner_path_result = next((item for item in path_results if item["learner_id"] == profile.learner_id), None)
            
            if not learner_path_result or not learner_path_result["result"].get("learning_path"):
                logger.warning(f"No learning path found for {profile.name}, skipping tutoring.")
                continue

            learning_path = learner_path_result["result"]["learning_path"]
            # Use the first concept in the path for testing
            target_concept = learning_path[0]
            concept_id = target_concept.get("concept", "unknown_concept")
            concept_name = target_concept.get("concept_name", "Unknown Concept")
            
            # Dynamic questions based on the concept
            sample_questions = [
                f"What is the main purpose of {concept_name}?",
                f"Can you give me an example of using {concept_name}?"
            ]

            for i, question in enumerate(sample_questions[:sessions_per_learner]):
                logger.info(f"Tutoring {profile.name} - Session {i+1} on {concept_name}")
                
                start_time = time.time()
                try:
                    if self.use_baseline:
                        # Baseline Execution
                        result = await agent.answer_question(
                            question=question,
                            context_override=None,
                            learner_profile={"name": profile.name},
                            force_real=self.use_real_llm
                        )
                        # Normalize output for metrics/logging
                        if "answer" in result:
                            result["guidance"] = result["answer"]
                    else:
                        # Socratic Execution
                        tutor_input = TutorInput(
                            learner_id=profile.learner_id,
                            question=question,
                            concept_id=concept_id,
                            hint_level=1,
                            force_real=self.use_real_llm
                        )
                        result = await agent.execute(tutor_input=tutor_input)
                    
                    latency_ms = (time.time() - start_time) * 1000
                    self.metrics.record_call("tutor", latency_ms, True, {
                        "learner_name": profile.name,
                        "session": i + 1,
                        "concept": concept_name
                    })
                    
                    sessions.append({
                        "learner_id": profile.learner_id,
                        "session": i + 1,
                        "question": question,
                        "concept_id": concept_id,
                        "result": result if isinstance(result, dict) else {"raw": str(result)},
                    })
                    
                except Exception as e:
                    latency_ms = (time.time() - start_time) * 1000
                    self.metrics.record_call("tutor", latency_ms, False, {"error": str(e)})
                    logger.error(f"Error in tutoring session: {e}")
                    sessions.append({"learner_id": profile.learner_id, "session": i + 1, "error": str(e)})
        
        return {"sessions_count": len(sessions), "items": sessions}
    
    async def run_phase_5_evaluation(self, profiles: List[LearnerProfile]) -> Dict:
        """Phase 5: Evaluate learner responses."""
        logger.info("=" * 60)
        logger.info("Phase 5: Evaluation (JudgeLM)")
        logger.info("=" * 60)
        
        from backend.agents.evaluator_agent import EvaluatorAgent
        
        agent = EvaluatorAgent(
            agent_id="exp_evaluator",
            state_manager=self.state_manager,
            event_bus=self.event_bus
        )
        
        evaluations = []
        
        for profile in profiles:
            # 1. Get generated path for this learner
            path_results = self.results.get("phases", {}).get("3_path_planning", {}).get("items", [])
            learner_path_result = next((item for item in path_results if item["learner_id"] == profile.learner_id), None)
            
            if not learner_path_result or not learner_path_result["result"].get("learning_path"):
                logger.warning(f"No learning path found for {profile.name}, skipping evaluation.")
                continue

            learning_path = learner_path_result["result"]["learning_path"]
            target_concept = learning_path[0]
            concept_id = target_concept.get("concept", "unknown_concept")
            concept_name = target_concept.get("concept_name", "Unknown Concept")

            # Dynamic responses based on the concept
            sample_responses = [
                (f"{concept_name} is used to store data.", f"{concept_name} allows storing and manipulating values."),
                (f"I don't know what {concept_name} is.", f"{concept_name} is a fundamental concept in this topic."),
            ]
            
            for i, (learner_resp, expected) in enumerate(sample_responses):
                logger.info(f"Evaluating {profile.name} - Response {i+1} on {concept_name}")
                
                start_time = time.time()
                try:
                    eval_input = EvaluationInput(
                        learner_id=profile.learner_id,
                        concept_id=concept_id,
                        learner_response=learner_resp,
                        expected_answer=expected,
                        force_real=self.use_real_llm
                    )
                    
                    result = await agent.execute(evaluation_input=eval_input)
                    
                    latency_ms = (time.time() - start_time) * 1000
                    self.metrics.record_call("evaluator", latency_ms, True, {
                        "learner_name": profile.name,
                        "concept": concept_name
                    })
                    
                    evaluations.append({
                        "learner_id": profile.learner_id,
                        "response_num": i + 1,
                        "concept_id": concept_id,
                        "result": result if isinstance(result, dict) else {"raw": str(result)},
                    })
                    
                except Exception as e:
                    latency_ms = (time.time() - start_time) * 1000
                    self.metrics.record_call("evaluator", latency_ms, False, {"error": str(e)})
                    logger.error(f"Error in evaluation: {e}")
                    evaluations.append({"learner_id": profile.learner_id, "error": str(e)})
        
        return {"evaluations_count": len(evaluations), "items": evaluations}
    
    async def run(self):
        """Execute the full experiment pipeline."""
        logger.info("=" * 60)
        logger.info("🔬 Starting Full-Scale Experiment")
        logger.info("=" * 60)
        
        # Load configuration and data
        config = self.load_experiment_config()
        profiles = self.load_learner_profiles()
        materials = self.load_course_materials()
        
        logger.info(f"Loaded {len(materials)} course materials")
        logger.info(f"Loaded {len(profiles)} learner profiles")
        logger.info(f"Using {'REAL' if self.use_real_llm else 'MOCK'} LLM")
        
        # Run phases
        self.results["phases"]["1_knowledge_extraction"] = await self.run_phase_1_knowledge_extraction(materials[:1])  # Limit to 1 for rate limits
        self.results["phases"]["2_profiling"] = await self.run_phase_2_profiling(profiles)
        self.results["phases"]["3_path_planning"] = await self.run_phase_3_path_planning(profiles)
        self.results["phases"]["4_tutoring"] = await self.run_phase_4_tutoring(profiles, sessions_per_learner=2)
        self.results["phases"]["5_evaluation"] = await self.run_phase_5_evaluation(profiles)
        
        # Collect final metrics
        self.results["completed_at"] = datetime.now().isoformat()
        self.results["metrics"] = self.metrics.get_summary()
        
        # Save results
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        results_file = RESULTS_DIR / f"experiment_{self.results['experiment_id'][:8]}.json"
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info("=" * 60)
        logger.info("✅ Experiment Complete!")
        logger.info("=" * 60)
        logger.info(f"Results saved to: {results_file}")
        
        # Print summary
        summary = self.metrics.get_summary()
        try:
            print("\nMetrics Summary:")
        except UnicodeEncodeError:
            print("\nMetrics Summary:")
        print(f"  Duration: {summary['experiment_duration_seconds']:.2f} seconds")
        for agent, stats in summary["agents"].items():
            print(f"  {agent}: {stats['total_calls']} calls, {stats['avg_latency_ms']:.0f}ms avg, {stats['success_rate']*100:.0f}% success")
        
        return self.results


# =============================================
# MAIN ENTRY POINT
# =============================================

def main():
    parser = argparse.ArgumentParser(description="Run Full-Scale Experiment")
    parser.add_argument("--real", action="store_true", help="Use real LLM instead of mock")
    parser.add_argument("--baseline", action="store_true", help="Use Baseline Agent (Control Group)")
    parser.add_argument("--learner", type=str, help="Filter to specific learner (e.g., 'alice')")
    args = parser.parse_args()
    
    runner = ExperimentRunner(
        use_real_llm=args.real,
        learner_filter=args.learner,
        use_baseline=args.baseline
    )
    
    asyncio.run(runner.run())


if __name__ == "__main__":
    main()
