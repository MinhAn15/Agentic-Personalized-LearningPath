import logging
import random  # FIX Issue 2: Moved import to top
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.harvard_enforcer import Harvard7Enforcer
from backend.models.dialogue import DialogueState, DialoguePhase, ScaffoldingLevel, UserIntent
from backend.config import get_settings
from backend.core.constants import (
    TUTOR_W_DOC,
    TUTOR_W_KG,
    TUTOR_W_PERSONAL,
    TUTOR_CONFIDENCE_THRESHOLD,
    TUTOR_CONFLICT_THRESHOLD,
    TUTOR_CONFLICT_PENALTY,
    TUTOR_COT_TRACES,
    TUTOR_CONSENSUS_THRESHOLD,
    TUTOR_LEAKAGE_KEYWORDS
)
from backend.core.llm_factory import LLMFactory
from llama_index.core import StorageContext, load_index_from_storage, Settings
import os

logger = logging.getLogger(__name__)



# UPGRADE: SocraticState removed in favor of Dynamic CoT (Wei 2022)
# class SocraticState(str, Enum):
#     ...



class TutorAgent(BaseAgent):
    """
    Tutor Agent - Teach using Harvard 7 Principles & Reverse Socratic Method.
    ...
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        super().__init__(agent_id, AgentType.TUTOR, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or LLMFactory.get_llm()
        
        # Configure LlamaIndex Global Settings for Query Embedding
        Settings.llm = self.llm
        Settings.embed_model = LLMFactory.get_embedding_model()

        self.logger = logging.getLogger(f"TutorAgent.{agent_id}")
        
        # Harvard 7 Enforcer for response quality
        self.harvard_enforcer = Harvard7Enforcer()
        
        # Dialogue states per (learner_id, concept_id)
        self.dialogue_states: Dict[Tuple[str, str], DialogueState] = {}
        
        # Confidence weights for 3-layer grounding (Now from constants)
        self.W_DOC = TUTOR_W_DOC
        self.W_KG = TUTOR_W_KG
        self.W_PERSONAL = TUTOR_W_PERSONAL
        self.CONFIDENCE_THRESHOLD = TUTOR_CONFIDENCE_THRESHOLD
        
        # Conflict detection threshold (semantic similarity < this = conflict)
        self.CONFLICT_THRESHOLD = TUTOR_CONFLICT_THRESHOLD
        self.CONFLICT_PENALTY = TUTOR_CONFLICT_PENALTY
        
        # Event subscriptions
        if event_bus and hasattr(event_bus, 'subscribe'):
            event_bus.subscribe('PATH_PLANNED', self._on_path_planned)
            event_bus.subscribe('EVALUATION_COMPLETED', self._on_evaluation_completed)
            self.logger.info("Subscribed to PATH_PLANNED, EVALUATION_COMPLETED")
            
        # Initialize RAG Query Engine
        self.query_engine = self._load_vector_index()

    def _load_vector_index(self):
        """Load local vector index if available"""
        try:
            # Safe path resolution
            storage_dir = os.path.join(os.getcwd(), "backend", "storage", "vector_store")
            docstore_path = os.path.join(storage_dir, "docstore.json")
            
            if os.path.exists(docstore_path):
                self.logger.info(f"📚 Loading vector index from {storage_dir}")
                storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
                index = load_index_from_storage(storage_context)
                # Enable async for non-blocking
                return index.as_query_engine(use_async=True)
            else:
                self.logger.warning(f"⚠️ Vector store not found at {storage_dir}. RAG will be disabled.")
                return None
        except Exception as e:
            self.logger.error(f"Failed to load vector index: {e}")
            return None
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Main execution method."""
        try:
            learner_id = kwargs.get("learner_id")
            question = kwargs.get("question")
            concept_id = kwargs.get("concept_id")
            # Force Real Mode override
            force_real = kwargs.get("force_real", False)
            
            # FIX: Validate hint_level range (0-4)
            hint_level = kwargs.get("hint_level", 0)
            hint_level = min(4, max(0, int(hint_level)))  # Clamp to valid range
            
            # Conversation history check
            conversation_history = kwargs.get("conversation_history", [])
            if not isinstance(conversation_history, list):
                 conversation_history = []

            # ---------------------------------------------------------------
            # HYBRID ARCHITECTURE: State Machine + CoT
            # ---------------------------------------------------------------
            
            # 1. Get or Create Dialogue State
            state = self._get_or_create_dialogue_state(learner_id, concept_id)
            state.turn_count += 1
            
            # 2. Check for Handoff (Assessment Phase)
            if state.phase == DialoguePhase.ASSESSMENT:
                await self._handoff_to_evaluator(learner_id, concept_id, state)
                return {
                    "response": "I've noticed you're doing great! Let's verify your mastery with a quick quiz.",
                    "action": "HANDOFF_TO_EVALUATOR"
                }

            # 3. Determine Response Strategy based on Phase
            response_text = ""
            
            if state.phase == DialoguePhase.EXPLANATION:
                # Use Standard Prompting for lightweight phases
                response_text = await self._generate_probing_question(question, state, force_real=force_real)
                # Heuristic transition: If student answers probe, check advancement
                if state.should_advance_phase():
                    state.advance_phase()
                    
            elif state.phase == DialoguePhase.QUESTIONING:
                # -------------------------------------------------------------
                # DYNAMIC CoT SCAFFOLDING (Wei 2022) with Slicing Logic
                # -------------------------------------------------------------
                
                # Check if we already have an active trace for this concept/misconception
                if not state.current_cot_trace:
                     # Generate NEW Hidden CoT Traces
                     traces = await self._generate_cot_traces(question, conversation_history, concept_id, force_real=force_real)
                     best_trace = self._check_consensus(traces)
                     
                     if best_trace:
                         # SLICING LOGIC: Split trace into scaffolding steps
                         # We expect the trace to be formatted as "1. ... 2. ... 3. ..." or similar.
                         # We'll split by newlines or numbered lists.
                         steps = self._slice_cot_trace(best_trace)
                         state.current_cot_trace = steps
                         state.cot_step_index = 0
                     else:
                         # Fallback if CoT fails
                         response_text = "Could you break that down into smaller steps?"
                
                # Serve the next step in the trace
                if state.current_cot_trace and state.cot_step_index < len(state.current_cot_trace):
                    raw_step = state.current_cot_trace[state.cot_step_index]
                    response_text = self._format_scaffold_step(raw_step, state.cot_step_index)
                    state.cot_step_index += 1
                else:
                    # Trace finished, check if understanding is clear? 
                    # For now, generic prompt.
                    response_text = "How does that explanation feel? Do you see how the pieces fit?"


            # 4. Update Interaction Log
            state.interaction_log.append({"role": "user", "content": question})
            state.interaction_log.append({"role": "assistant", "content": response_text})

            return {
                "success": True,
                "guidance": response_text,
                "current_phase": state.phase.value,
                "hint_level": 1, # Default/Placeholder
                "source": "Socratic Tutor"
            }
        except Exception as e:
            self.logger.error(f"Tutor execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }

    async def _generate_probing_question(self, question: str, state: DialogueState, force_real: bool = False) -> str:
        """Lightweight prompt for Intro/Probing phases"""
        if self.settings.MOCK_LLM and not force_real:
             return f"Create a probing question about {state.concept_id} based on '{question}'? (Mock)"

        prompt = f"""
        Act as a Socratic Tutor.
        Context: Learner {state.learner_id} is asking about {state.concept_id}.
        Phase: {state.phase.value}
        Student Question: {question}
        
        Goal: Ask a guiding question to check understanding without giving the answer.
        Keep it short (1-2 sentences).
        """
        response = await self.llm.acomplete(prompt)
        return response.text

    async def _generate_cot_traces(self, question: str, history: List[Dict], concept_id: str, n: int = TUTOR_COT_TRACES, force_real: bool = False) -> List[str]:
        """
        Generate n internal reasoning traces (Internal Monologue).
        Uses Exemplars from Wei et al. (2022) to elicit reasoning.
        """
        if self.settings.MOCK_LLM and not force_real:
            return [
                f"CoT: Analyze {question}. The student needs help with {concept_id}. Student Hint: Think about the definition of {concept_id}."
            ]

        if not self.llm:
            return []
            
        # SOTA PROMPTING STRATEGY via NotebookLM Audit
        prompt = f"""
        Instruction: You are a Tutor. Solve the problem step-by-step to identify the logic, but DO NOT reveal the answer to the student yet.

        [Exemplar 1: Math/Logic]
        Q: Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?
        CoT: Roger started with 5 balls. 2 cans of 3 tennis balls each is 6 tennis balls. 5 + 6 = 11.
        Student Hint: First, calculate how many balls are in the new cans.

        [Exemplar 2: Commonsense]
        Q: Would a pear sink in water?
        CoT: The density of a pear is about 0.6 g/cm^3, which is less than water. Objects less dense than water float. Thus, a pear would float.
        Student Hint: Think about the density of the pear compared to water.

        [Exemplar 3: Coding]
        Q: My recursion function errors with 'maximum depth exceeded'.
        CoT: Recursion requires a base case to stop. Infinite recursion happens if the base case is missing or unreachable. The student likely forgot the base case.
        Student Hint: Check your function for a stop condition. Does it handle the simplest case?

        [Current Interaction]
        Q: {question}
        Concept Context: {concept_id}
        Conversation History: {str(history[-3:] if history else [])}
        
        Task: Diagnose the student's misunderstanding.
        Output Format:
        CoT: [Internal reasoning trace about the error]
        Student Hint: [The first scaffolding step]
        """
        try:
             # Simulation of multiple calls (in production, run in parallel)
             traces = []
             for _ in range(n):
                 response = await self.llm.acomplete(prompt)
                 traces.append(response.text)
             return traces
        except Exception as e:
            self.logger.error(f"CoT generation failed: {e}")
            return []

    def _slice_cot_trace(self, trace: str) -> List[str]:
        """
        Slice the CoT trace into steps. 
        Note: The Exemplar prompts usually produce a single 'Student Hint'.
        However, if the CoT is complex, we might want to break it down.
        For V1 (Exemplar based), we mostly map 'Student Hint' as step 1.
        If we want multi-step, we'd need the prompt to output Step 1, Step 2.
        
        Let's try to extract 'Student Hint' and any logic from 'CoT' that is safe.
        """
        steps = []
        
        # 1. Extract the explicit "Student Hint"
        if "Student Hint:" in trace:
            hint = trace.split("Student Hint:")[1].strip()
            steps.append(hint)
        
        # 2. (Optional) If we want more steps, we could process the CoT part 
        # but the prompt structure currently focuses on ONE main hint.
        # Future refinement: Chain hints.
        
        if not steps:
            # Fallback cleanup
            steps.append(self._extract_scaffold(trace))
            
        return steps

    def _format_scaffold_step(self, step_content: str, index: int) -> str:
        """Format the step for the user"""
        return f"Hint: {step_content}"

    def _check_consensus(self, traces: List[str]) -> Optional[str]:
        """
        Metacognitive Check: Self-Consistency (Wang 2022).
        For V1, pick the trace that follows the format 'CoT:... Student Hint:...'
        """
        if not traces:
            return None
        
        valid_traces = [t for t in traces if "Student Hint:" in t]
        if not valid_traces:
            return max(traces, key=len) # Fallback to longest
            
        # Placeholder: Return the first valid one as 'best'
        return valid_traces[0]

    def _extract_scaffold(self, trace: str) -> str:
        """
        Leakage Guard: Remove 'final answer' markers.
        """
        if "Student Hint:" in trace:
            return trace.split("Student Hint:")[1].strip()
            
        # Fallback: Heuristic cleaning
        lines = trace.split('\n')
        safe_lines = []
        for line in lines:
            is_leak = False
            for keyword in TUTOR_LEAKAGE_KEYWORDS:
                if keyword in line or keyword.lower() in line.lower():
                    is_leak = True
                    break
            if not is_leak:
                safe_lines.append(line)
        
        scaffold = "\n".join(safe_lines).strip()
        return f"Let's think about this:\n{scaffold}\n\nWhat are your thoughts?"
            

    
    async def _get_concept_from_kg(self, concept_id: str) -> Optional[Dict]:
        """Get concept details from Course KG"""
        neo4j = self.state_manager.neo4j
        result = await neo4j.run_query(
            """
            MATCH (c:CourseConcept {concept_id: $concept_id})
            OPTIONAL MATCH (c)-[:REQUIRES]->(prereq:CourseConcept)
            OPTIONAL MATCH (c)<-[:IS_SUB_CONCEPT_OF]-(sub:CourseConcept)
            RETURN c, collect(DISTINCT prereq.name) as prerequisites,
                   collect(DISTINCT sub.name) as subconcepts
            """,
            concept_id=concept_id
        )
        
        if result and result[0].get("c"):
            concept_data = result[0]["c"]
            return {
                **concept_data,
                "prerequisites": result[0].get("prerequisites", []),
                "subconcepts": result[0].get("subconcepts", [])
            }
        return None
    
    async def _get_learner_state(self, learner_id: str, concept_id: str) -> Dict:
        """Get learner state from Personal KG"""
        neo4j = self.state_manager.neo4j
        result = await neo4j.run_query(
            """
            MATCH (l:Learner {learner_id: $learner_id})
            OPTIONAL MATCH (l)-[m:HAS_MASTERY]->(c:CourseConcept {concept_id: $concept_id})
            OPTIONAL MATCH (l)-[:HAS_MISCONCEPTION]->(e:ErrorNode)-[:ABOUT]->(c)
            OPTIONAL MATCH (l)-[:CREATED_NOTE]->(n:NoteNode)-[:ABOUT]->(c)
            RETURN l.learning_style as learning_style,
                   m.level as mastery, 
                   collect(DISTINCT e.description) as misconceptions,
                   collect(DISTINCT n.content) as notes
            """,
            learner_id=learner_id,
            concept_id=concept_id
        )
        
        if result:
            return {
                "learning_style": result[0].get("learning_style", "VISUAL"),  # FIX Issue 3
                "mastery": result[0].get("mastery", 0.0) or 0.0,
                "misconceptions": result[0].get("misconceptions", []),
                "notes": result[0].get("notes", [])
            }
        return {"learning_style": "VISUAL", "mastery": 0.0, "misconceptions": [], "notes": []}
    

    async def _course_kg_retrieve(self, concept_id: str) -> tuple:
        """Layer 2: Retrieve from Course Knowledge Graph"""
        try:
            neo4j = self.state_manager.neo4j
            result = await neo4j.run_query(
                """
                MATCH (c:CourseConcept {concept_id: $concept_id})
                OPTIONAL MATCH (c)-[:REQUIRES]->(prereq)
                OPTIONAL MATCH (c)-[:SIMILAR_TO]-(similar)
                OPTIONAL MATCH (c)-[:HAS_ALTERNATIVE_PATH]-(alt)
                RETURN c.name as name,
                       c.description as definition,
                       c.examples as examples,
                       c.common_misconceptions as misconceptions,
                       collect(DISTINCT prereq.name) as prerequisites,
                       collect(DISTINCT similar.name) as similar_concepts,
                       collect(DISTINCT alt.name) as alternative_paths
                """,
                concept_id=concept_id
            )
            
            if result:
                context = {
                    "name": result[0].get("name"),
                    "definition": result[0].get("definition"),
                    "examples": result[0].get("examples", []),
                    "misconceptions": result[0].get("misconceptions", []),
                    "prerequisites": result[0].get("prerequisites", []),
                    "similar_concepts": result[0].get("similar_concepts", []),
                    "alternative_paths": result[0].get("alternative_paths", [])
                }
                
                # FIX Issue 1: Dynamic score based on data completeness
                # Score reflects how much structured knowledge we have
                score_factors = [
                    0.3 if context["definition"] else 0.0,  # Definition is critical
                    0.2 if context["examples"] else 0.0,     # Examples help learning
                    0.2 if context["misconceptions"] else 0.0,  # Anti-hallucination
                    0.15 if context["prerequisites"] else 0.0,  # Context
                    0.15 if context["similar_concepts"] else 0.0  # Related knowledge
                ]
                score = sum(score_factors)
                
                return context, score
            
            return {}, 0.0
        except Exception as e:
            self.logger.error(f"Course KG retrieval error: {e}")
            return {}, 0.0
    
    async def _personal_kg_retrieve(self, learner_id: str, concept_id: str) -> tuple:
        """Layer 3: Retrieve from Personal Knowledge Graph"""
        try:
            neo4j = self.state_manager.neo4j
            result = await neo4j.run_query(
                """
                MATCH (l:Learner {learner_id: $learner_id})
                OPTIONAL MATCH (l)-[m:HAS_MASTERY]->(c:CourseConcept {concept_id: $concept_id})
                OPTIONAL MATCH (l)-[:HAS_MISCONCEPTION]->(e:ErrorNode)-[:ABOUT]->(c)
                OPTIONAL MATCH (l)-[:CREATED_NOTE]->(n:NoteNode)-[:ABOUT]->(c)
                RETURN l.learning_style as learning_style,
                       m.level as mastery_level,
                       collect(DISTINCT e.description) as past_errors,
                       collect(DISTINCT n.content) as personal_notes
                """,
                learner_id=learner_id,
                concept_id=concept_id
            )
            
            if result:
                context = {
                    "learning_style": result[0].get("learning_style"),
                    "mastery_level": result[0].get("mastery_level"),
                    "past_errors": result[0].get("past_errors", []),
                    "personal_notes": result[0].get("personal_notes", [])
                }
                
                # Higher score if we have personal data
                has_data = any([
                    context["mastery_level"],
                    context["past_errors"],
                    context["personal_notes"]
                ])
                score = 0.8 if has_data else 0.3
                
                return context, score
            
            return {}, 0.0
        except Exception as e:
            self.logger.error(f"Personal KG retrieval error: {e}")
            return {}, 0.0
    

    
    async def _on_path_planned(self, event: Dict):
        """Handle path_planned event from Agent 3"""
        try:
            learner_id = event.get('learner_id')
            concept_id = event.get('current_concept')
            
            if learner_id and concept_id:
                # Reset dialogue state for new concept
                key = (learner_id, concept_id)
                if key in self.dialogue_states:
                    del self.dialogue_states[key]
                
                self.logger.info(f"PATH_PLANNED: Reset state for {learner_id}/{concept_id}")
        except Exception as e:
            self.logger.error(f"Error handling PATH_PLANNED: {e}")
    
    async def _on_evaluation_completed(self, event: Dict):
        """Handle evaluation result from Agent 5"""
        try:
            learner_id = event.get('learner_id')
            concept_id = event.get('concept_id')
            key = (learner_id, concept_id)
            
            if key in self.dialogue_states:
                # Update misconceptions from Evaluator
                for misc in event.get('misconceptions', []):
                    self.dialogue_states[key].suspected_misconceptions.append(misc)
                
                self.logger.info(f"EVALUATION_COMPLETED: Updated misconceptions for {learner_id}/{concept_id}")
        except Exception as e:
            self.logger.error(f"Error handling EVALUATION_COMPLETED: {e}")
    
    async def _handoff_to_evaluator(self, learner_id: str, concept_id: str, state: DialogueState):
        """Handoff to Evaluator Agent when reaching ASSESSMENT phase"""
        if self.event_bus:
            await self.send_message(
                receiver="evaluator",
                message_type="TUTOR_ASSESSMENT_READY",
                payload={
                    'learner_id': learner_id,
                    'concept_id': concept_id,
                    'dialogue_transcript': state.interaction_log,
                    'suspected_misconceptions': state.suspected_misconceptions,
                    'total_turns': state.turn_count
                }
            )
            self.logger.info(f"Handoff to Evaluator: {learner_id}/{concept_id}")
    
    def _get_or_create_dialogue_state(self, learner_id: str, concept_id: str, 
                                      learning_style: str = "VISUAL") -> DialogueState:
        """Get existing dialogue state or create new one"""
        key = (learner_id, concept_id)
        if key not in self.dialogue_states:
            self.dialogue_states[key] = DialogueState(
                learner_id=learner_id,
                concept_id=concept_id,
                learning_style=learning_style
            )
        return self.dialogue_states[key]
    
    def enforce_harvard_principles(self, response: str, learning_style: str, 
                                   phase: str) -> str:
        """Apply Harvard 7 Principles to response using enforcer"""
        return self.harvard_enforcer.enforce(
            response=response,
            learner_context={'learning_style': learning_style},
            phase=phase
        )

