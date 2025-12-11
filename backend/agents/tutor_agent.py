import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from backend.core.base_agent import BaseAgent, AgentType
from backend.config import get_settings
from llama_index.llms.gemini import Gemini

logger = logging.getLogger(__name__)


class SocraticState(str, Enum):
    """
    Reverse Socratic State Machine (5 States) per Thesis
    
    State 0: PROBING - Ask open-ended question about concept
    State 1: SCAFFOLDING - Provide hint level 1 (conceptual)
    State 2: GUIDING - Provide hint level 2 (structural)
    State 3: EXPLAINING - Provide partial explanation + ask to complete
    State 4: CONCLUSION - Synthesize correct answer + learner's insight
    """
    PROBING = "PROBING"           # State 0
    SCAFFOLDING = "SCAFFOLDING"   # State 1
    GUIDING = "GUIDING"           # State 2
    EXPLAINING = "EXPLAINING"     # State 3
    CONCLUSION = "CONCLUSION"     # State 4


class TutorAgent(BaseAgent):
    """
    Tutor Agent - Teach using Harvard 7 Principles & Reverse Socratic Method.
    
    Features (per Thesis):
    1. Reverse Socratic State Machine (5 states)
    2. 3-Layer Grounding (RAG + Course KG + Personal KG)
    3. Harvard 7 Principles enforcement
    4. Cognitive Load Management (2-4 sentences max)
    5. Confidence Scoring for hallucination prevention
    
    Process Flow:
    1. Receive learner question + concept context
    2. Determine current Socratic state
    3. 3-Layer Grounding:
       - Layer 1: Document Grounding (RAG from Chroma)
       - Layer 2: Course KG Grounding (Neo4j)
       - Layer 3: Personal KG Grounding
    4. Calculate confidence score
    5. Generate Socratic response per current state
    6. Apply Harvard 7 Principles
    7. Return guidance with confidence
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        super().__init__(agent_id, AgentType.TUTOR, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or Gemini(
            model=self.settings.GEMINI_MODEL,
            api_key=self.settings.GOOGLE_API_KEY
        )
        self.logger = logging.getLogger(f"TutorAgent.{agent_id}")
        
        # Confidence weights for 3-layer grounding
        self.W_DOC = 0.4   # Document grounding weight
        self.W_KG = 0.35   # Course KG weight
        self.W_PERSONAL = 0.25  # Personal KG weight
        self.CONFIDENCE_THRESHOLD = 0.5
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Main execution method."""
        try:
            learner_id = kwargs.get("learner_id")
            question = kwargs.get("question")
            concept_id = kwargs.get("concept_id")
            hint_level = kwargs.get("hint_level", 0)
            conversation_history = kwargs.get("conversation_history", [])
            
            if not all([learner_id, question, concept_id]):
                return {
                    "success": False,
                    "error": "learner_id, question, and concept_id required",
                    "agent_id": self.agent_id
                }
            
            self.logger.info(f"👨‍🏫 Tutoring {learner_id} on {concept_id}")
            
            # Step 1: Get concept details from Course KG
            concept = await self._get_concept_from_kg(concept_id)
            if not concept:
                return {
                    "success": False,
                    "error": f"Concept not found: {concept_id}",
                    "agent_id": self.agent_id
                }
            
            # Step 2: Get learner's current state from Personal KG
            learner_state = await self._get_learner_state(learner_id, concept_id)
            current_mastery = learner_state.get("mastery", 0.0)
            
            # Step 3: Determine Socratic state
            socratic_state = self._determine_socratic_state(
                hint_level=hint_level,
                current_mastery=current_mastery,
                conversation_turns=len(conversation_history)
            )
            
            # Step 4: 3-Layer Grounding
            grounding_result = await self._three_layer_grounding(
                query=question,
                concept_id=concept_id,
                learner_id=learner_id
            )
            
            # Step 5: Check confidence threshold
            if grounding_result["confidence"] < self.CONFIDENCE_THRESHOLD:
                return {
                    "success": True,
                    "agent_id": self.agent_id,
                    "learner_id": learner_id,
                    "concept_id": concept_id,
                    "guidance": "I'm not entirely sure based on the available course materials. Let me rephrase: What specific aspect of this concept would you like to explore?",
                    "grounded": False,
                    "confidence": grounding_result["confidence"],
                    "socratic_state": socratic_state.value,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 6: Generate Socratic response
            response = await self._generate_socratic_response(
                question=question,
                concept=concept,
                grounding_context=grounding_result["context"],
                learner_state=learner_state,
                socratic_state=socratic_state,
                conversation_history=conversation_history
            )
            
            if not response.get("success"):
                return response
            
            # Step 7: Prepare result
            result = {
                "success": True,
                "agent_id": self.agent_id,
                "learner_id": learner_id,
                "concept_id": concept_id,
                "guidance": response["guidance"],
                "follow_up_question": response.get("follow_up_question"),
                "socratic_state": socratic_state.value,
                "next_state": self._get_next_state(socratic_state).value,
                "grounded": True,
                "confidence": grounding_result["confidence"],
                "grounding_sources": grounding_result["sources"],
                "hint_level": self._state_to_hint_level(socratic_state),
                "timestamp": datetime.now().isoformat()
            }
            
            # Step 8: Save session state
            await self.save_state(
                f"tutor_session:{learner_id}:{concept_id}",
                {
                    "last_guidance": result,
                    "socratic_state": socratic_state.value,
                    "conversation_turns": len(conversation_history) + 1
                }
            )
            
            # Step 9: Emit event for evaluator
            await self.send_message(
                receiver="evaluator",
                message_type="tutor_guidance_provided",
                payload={
                    "learner_id": learner_id,
                    "concept_id": concept_id,
                    "socratic_state": socratic_state.value,
                    "hint_level": result["hint_level"]
                }
            )
            
            self.logger.info(f"✅ Guidance provided (state: {socratic_state.value}, confidence: {grounding_result['confidence']:.2f})")
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ Tutoring failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
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
            RETURN m.level as mastery, 
                   collect(DISTINCT e.description) as misconceptions,
                   collect(DISTINCT n.content) as notes
            """,
            learner_id=learner_id,
            concept_id=concept_id
        )
        
        if result:
            return {
                "mastery": result[0].get("mastery", 0.0) or 0.0,
                "misconceptions": result[0].get("misconceptions", []),
                "notes": result[0].get("notes", [])
            }
        return {"mastery": 0.0, "misconceptions": [], "notes": []}
    
    def _determine_socratic_state(
        self,
        hint_level: int,
        current_mastery: float,
        conversation_turns: int
    ) -> SocraticState:
        """
        Determine current Socratic state based on context.
        
        State transitions:
        - High mastery + low turns -> PROBING (challenge them)
        - Increasing hints -> SCAFFOLDING -> GUIDING -> EXPLAINING
        - After explanation -> CONCLUSION
        """
        # Map hint levels to states
        if hint_level >= 4 or conversation_turns >= 5:
            return SocraticState.CONCLUSION
        elif hint_level >= 3:
            return SocraticState.EXPLAINING
        elif hint_level >= 2:
            return SocraticState.GUIDING
        elif hint_level >= 1:
            return SocraticState.SCAFFOLDING
        else:
            return SocraticState.PROBING
    
    def _get_next_state(self, current_state: SocraticState) -> SocraticState:
        """Get next state in Socratic progression"""
        state_order = [
            SocraticState.PROBING,
            SocraticState.SCAFFOLDING,
            SocraticState.GUIDING,
            SocraticState.EXPLAINING,
            SocraticState.CONCLUSION
        ]
        current_idx = state_order.index(current_state)
        next_idx = min(current_idx + 1, len(state_order) - 1)
        return state_order[next_idx]
    
    def _state_to_hint_level(self, state: SocraticState) -> int:
        """Convert Socratic state to hint level"""
        mapping = {
            SocraticState.PROBING: 0,
            SocraticState.SCAFFOLDING: 1,
            SocraticState.GUIDING: 2,
            SocraticState.EXPLAINING: 3,
            SocraticState.CONCLUSION: 4
        }
        return mapping.get(state, 0)
    
    async def _three_layer_grounding(
        self,
        query: str,
        concept_id: str,
        learner_id: str
    ) -> Dict[str, Any]:
        """
        3-Layer Grounding System per Thesis.
        
        Layer 1: Document Grounding (RAG from Chroma)
        Layer 2: Course KG Grounding (Neo4j)
        Layer 3: Personal KG Grounding
        """
        sources = []
        
        # Layer 1: Document Grounding (RAG)
        doc_context, doc_score = await self._rag_retrieve(query, concept_id)
        if doc_context:
            sources.append({"layer": "DOCUMENT", "score": doc_score})
        
        # Layer 2: Course KG Grounding
        kg_context, kg_score = await self._course_kg_retrieve(concept_id)
        if kg_context:
            sources.append({"layer": "COURSE_KG", "score": kg_score})
        
        # Layer 3: Personal KG Grounding
        personal_context, personal_score = await self._personal_kg_retrieve(learner_id, concept_id)
        if personal_context:
            sources.append({"layer": "PERSONAL_KG", "score": personal_score})
        
        # Calculate weighted confidence
        confidence = (
            self.W_DOC * doc_score +
            self.W_KG * kg_score +
            self.W_PERSONAL * personal_score
        )
        
        # Merge context
        merged_context = {
            "document": doc_context,
            "course_kg": kg_context,
            "personal": personal_context
        }
        
        return {
            "context": merged_context,
            "confidence": confidence,
            "sources": sources
        }
    
    async def _rag_retrieve(self, query: str, concept_id: str) -> tuple:
        """Layer 1: Retrieve from vector store (Chroma)"""
        try:
            # In production, query Chroma vector DB
            # For now, return placeholder with moderate score
            
            # TODO: Integrate with Chroma
            # chroma = self.state_manager.chroma
            # results = await chroma.query(query, concept_id)
            
            context = {
                "retrieved_chunks": [],
                "concept_definition": f"Definition related to {concept_id}",
                "examples": []
            }
            
            # Simulated score (would be actual similarity score)
            score = 0.6
            
            return context, score
        except Exception as e:
            self.logger.error(f"RAG retrieval error: {e}")
            return {}, 0.0
    
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
                score = 0.9 if context["definition"] else 0.5
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
    
    async def _generate_socratic_response(
        self,
        question: str,
        concept: Dict[str, Any],
        grounding_context: Dict[str, Any],
        learner_state: Dict[str, Any],
        socratic_state: SocraticState,
        conversation_history: List
    ) -> Dict[str, Any]:
        """Generate response following Socratic state machine"""
        try:
            # Build state-specific prompt
            prompt = self._build_socratic_prompt(
                concept=concept,
                grounding_context=grounding_context,
                learner_state=learner_state,
                socratic_state=socratic_state
            )
            
            # Build user message
            user_message = f"""
Learner's Question: {question}

Previous conversation: {len(conversation_history)} turns

Generate a Socratic response following the {socratic_state.value} state.
Keep response SHORT (2-4 sentences max).
"""
            
            response = await self.llm.acomplete(prompt + "\n\n" + user_message)
            response_text = response.text.strip()
            
            # Extract follow-up question if present
            follow_up = None
            if "?" in response_text:
                sentences = response_text.split(".")
                for s in sentences:
                    if "?" in s:
                        follow_up = s.strip()
                        break
            
            return {
                "success": True,
                "guidance": response_text,
                "follow_up_question": follow_up
            }
        
        except Exception as e:
            self.logger.error(f"Response generation error: {e}")
            return {"success": False, "error": str(e)}
    
    def _build_socratic_prompt(
        self,
        concept: Dict[str, Any],
        grounding_context: Dict[str, Any],
        learner_state: Dict[str, Any],
        socratic_state: SocraticState
    ) -> str:
        """Build prompt for Socratic response based on state"""
        
        # State-specific instructions
        state_instructions = {
            SocraticState.PROBING: """
STATE 0 - PROBING:
- Ask open-ended question to probe understanding
- "What do YOU think about...?"
- Don't give any hints yet
- Encourage them to formulate their own answer first
""",
            SocraticState.SCAFFOLDING: """
STATE 1 - SCAFFOLDING:
- Provide a CONCEPTUAL hint (high-level framework)
- "Think about it this way..."
- Still don't give the answer
- Ask a clarifying question
""",
            SocraticState.GUIDING: """
STATE 2 - GUIDING:
- Provide a STRUCTURAL hint (steps/process)
- "The first step is usually..."
- Point them in the right direction
- Ask them to continue the thought
""",
            SocraticState.EXPLAINING: """
STATE 3 - EXPLAINING:
- Provide PARTIAL explanation
- Give part of the answer but leave key insight for them
- "So X leads to Y because... can you complete this?"
- Still engage them to participate
""",
            SocraticState.CONCLUSION: """
STATE 4 - CONCLUSION:
- Synthesize the full correct answer
- Connect their insights with the correct concept
- Praise their effort and thinking process
- Summarize what they learned
"""
        }
        
        # Build grounded context
        kg_context = grounding_context.get("course_kg", {})
        personal_context = grounding_context.get("personal", {})
        
        prompt = f"""
You are an expert Socratic tutor using Harvard 7 Pedagogical Principles.

HARVARD 7 PRINCIPLES (ENFORCE ALL):
1. ❌ NEVER give direct answers - guide with questions
2. ✅ Keep responses SHORT (2-4 sentences MAX)
3. ✅ Reveal ONE STEP at a time
4. ✅ Ask "What do YOU think?" before helping
5. ✅ Praise EFFORT, not intelligence
6. ✅ Personalized feedback - address THEIR specific error
7. ✅ Ground ONLY in verified sources

CURRENT STATE:
{state_instructions[socratic_state]}

CONCEPT INFORMATION:
- Name: {concept.get('name', 'Unknown')}
- Definition: {kg_context.get('definition', 'Not available')}
- Examples: {kg_context.get('examples', [])}
- Common Misconceptions: {kg_context.get('misconceptions', [])}
- Prerequisites: {kg_context.get('prerequisites', [])}

LEARNER CONTEXT:
- Current Mastery: {learner_state.get('mastery', 0):.0%}
- Past Errors: {learner_state.get('misconceptions', [])}
- Learning Style: {personal_context.get('learning_style', 'VISUAL')}
- Personal Notes: {personal_context.get('personal_notes', [])}

RESPONSE RULES:
- 2-4 sentences MAXIMUM
- Follow the {socratic_state.value} state instructions
- Reference course materials, not speculation
- If learner has past errors, address them
- Adapt to their learning style
"""
        
        return prompt
