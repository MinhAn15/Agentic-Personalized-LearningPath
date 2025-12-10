import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.core.base_agent import BaseAgent, AgentType
from backend.config import get_settings
from llama_index.llms.openai import OpenAI

logger = logging.getLogger(__name__)

class TutorAgent(BaseAgent):
    """
    Tutor Agent - Teach using Socratic method (Harvard 7 Principles).
    
    Responsibility:
    - Answer learner questions about concepts
    - Guide thinking without giving direct answers
    - Detect misconceptions
    - Adapt teaching to learner level
    - Enforce Harvard 7 Pedagogical Principles
    
    Process Flow:
    1. Receive learner question + concept context
    2. Retrieve concept details from KG (difficulty, prerequisites)
    3. Retrieve relevant course materials via RAG
    4. Determine appropriate hint level
    5. Generate Socratic response (guide, don't tell)
    6. Enforce all 7 Harvard Principles
    7. Return guidance to learner
    8. Send to Evaluator for assessment
    
    Harvard 7 Principles (ENFORCE ALL):
    1. ❌ NEVER give direct answers - guide with questions
    2. ✅ Keep responses SHORT (2-4 sentences max)
    3. ✅ Reveal ONE STEP AT A TIME
    4. ✅ Ask "What do YOU think?" before helping
    5. ✅ Praise EFFORT, not intelligence
    6. ✅ Personalized feedback (address THEIR specific error)
    7. ✅ Ground ONLY in verified sources (RAG + KG)
    
    Example Flow:
        Learner: "What's a WHERE clause?"
            ↓
        Tutor: "Great question! Think about it this way:
        Imagine you have a list of 1000 people. You only want 
        to work with people over 21. What would you do first?"
            ↓
        Learner: "Filter them?"
            ↓
        Tutor: "Exactly! WHERE does the same thing with data.
        Can you think of how you might write a WHERE condition?"
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        """
        Initialize Tutor Agent.
        
        Args:
            agent_id: Unique agent identifier
            state_manager: Central state manager
            event_bus: Event bus for inter-agent communication
            llm: LLM instance (OpenAI by default)
        """
        super().__init__(agent_id, AgentType.TUTOR, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or OpenAI(
            model=self.settings.OPENAI_MODEL,
            api_key=self.settings.OPENAI_API_KEY
        )
        self.logger = logging.getLogger(f"TutorAgent.{agent_id}")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method - answer learner question with Socratic guidance.
        
        Args:
            learner_id: str - Learner ID
            question: str - Learner's question
            concept_id: str - Concept being learned
            hint_level: int - Current hint level (0-5, default 1)
            conversation_history: List - Previous Q&A
            
        Returns:
            Dict with Socratic guidance
        """
        try:
            learner_id = kwargs.get("learner_id")
            question = kwargs.get("question")
            concept_id = kwargs.get("concept_id")
            hint_level = kwargs.get("hint_level", 1)
            conversation_history = kwargs.get("conversation_history", [])
            
            if not all([learner_id, question, concept_id]):
                return {
                    "success": False,
                    "error": "learner_id, question, and concept_id required",
                    "agent_id": self.agent_id
                }
            
            self.logger.info(f"👨‍🏫 Tutoring {learner_id} on {concept_id}")
            
            # Step 1: Get concept details from KG
            neo4j = self.state_manager.neo4j
            concept_result = await neo4j.run_query(
                "MATCH (c:CourseConcept {concept_id: $concept_id}) RETURN c",
                concept_id=concept_id
            )
            
            if not concept_result:
                return {
                    "success": False,
                    "error": f"Concept not found: {concept_id}",
                    "agent_id": self.agent_id
                }
            
            concept = concept_result[0].get("c", {})
            
            # Step 2: Get learner's current mastery
            learner_profile = await self.state_manager.get_learner_profile(learner_id)
            current_mastery = 0.0
            if learner_profile:
                for mastery in learner_profile.get("current_mastery", []):
                    if mastery.get("concept_id") == concept_id:
                        current_mastery = mastery.get("mastery_level", 0.0)
                        break
            
            # Step 3: Retrieve context (RAG)
            context = await self._retrieve_context(concept_id, question)
            
            # Step 4: Determine hint level based on learner progress
            adjusted_hint = await self._determine_hint_level(
                current_mastery,
                concept.get("difficulty", 2),
                hint_level
            )
            
            # Step 5: Generate Socratic response
            response = await self._generate_socratic_response(
                question=question,
                concept=concept,
                context=context,
                learner_mastery=current_mastery,
                hint_level=adjusted_hint,
                conversation_history=conversation_history
            )
            
            if not response.get("success"):
                return response
            
            # Step 6: Prepare result
            result = {
                "success": True,
                "agent_id": self.agent_id,
                "learner_id": learner_id,
                "concept_id": concept_id,
                "guidance": response["guidance"],
                "hint_level": adjusted_hint,
                "follow_up_question": response.get("follow_up_question"),
                "source": response.get("source"),
                "timestamp": datetime.now().isoformat()
            }
            
            # Step 7: Save to conversation history
            await self.save_state(
                f"tutor_session:{learner_id}:{concept_id}",
                {
                    "last_guidance": result,
                    "conversation_turns": len(conversation_history) + 1
                }
            )
            
            # Step 8: Emit event for evaluator (when learner responds)
            await self.send_message(
                receiver="evaluator",
                message_type="tutor_guidance_provided",
                payload={
                    "learner_id": learner_id,
                    "concept_id": concept_id,
                    "hint_level": adjusted_hint
                }
            )
            
            self.logger.info(f"✅ Guidance provided (hint level {adjusted_hint})")
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ Tutoring failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    async def _retrieve_context(self, concept_id: str, question: str) -> Dict[str, Any]:
        """
        Retrieve relevant course materials using RAG.
        
        Args:
            concept_id: Concept being taught
            question: Learner's specific question
            
        Returns:
            Dict with relevant materials + examples
        """
        try:
            # In production, query Chroma vector DB for relevant passages
            # For now, return structured context
            
            return {
                "concept_id": concept_id,
                "relevant_materials": [],  # Would be populated from Chroma
                "examples": [],  # Would be examples from documents
                "common_misconceptions": [],  # Known misconceptions
                "prerequisite_topics": []  # Related prerequisites
            }
        except Exception as e:
            self.logger.error(f"Context retrieval error: {e}")
            return {}
    
    async def _determine_hint_level(
        self,
        current_mastery: float,
        concept_difficulty: int,
        requested_hint: int
    ) -> int:
        """
        Determine appropriate hint level based on learner progress.
        
        Hint levels:
        - 0: No hints (let them struggle - productive struggle)
        - 1: Gentle guidance (What do you think...?)
        - 2: Clarifying questions
        - 3: Partial example
        - 4: Full explanation
        - 5: Direct answer (last resort)
        
        Args:
            current_mastery: Learner's current mastery (0-1)
            concept_difficulty: Concept difficulty (1-5)
            requested_hint: Requested hint level
            
        Returns:
            Adjusted hint level (0-5)
        """
        # Start with requested level
        hint = requested_hint
        
        # Adjust based on mastery
        if current_mastery < 0.3:
            # Low mastery - provide more guidance
            hint = min(hint + 1, 5)
        elif current_mastery > 0.7:
            # High mastery - less guidance, more struggle
            hint = max(hint - 1, 0)
        
        return hint
    
    async def _generate_socratic_response(
        self,
        question: str,
        concept: Dict[str, Any],
        context: Dict[str, Any],
        learner_mastery: float,
        hint_level: int,
        conversation_history: List
    ) -> Dict[str, Any]:
        """
        Generate Socratic response following Harvard 7 Principles.
        
        Args:
            question: Learner's question
            concept: Concept details from KG
            context: Retrieved context from RAG
            learner_mastery: Learner's current mastery
            hint_level: Appropriate hint level
            conversation_history: Previous Q&A
            
        Returns:
            Dict with guidance response
        """
        try:
            # Build system prompt enforcing Harvard 7 Principles
            system_prompt = self._build_system_prompt(
                concept=concept,
                hint_level=hint_level,
                learner_mastery=learner_mastery
            )
            
            # Build user message with context
            user_message = f"""
            Concept: {concept.get('name', 'Unknown')}
            Learner's Question: {question}
            Learner's Current Mastery: {learner_mastery:.1%}
            Context: {context.get('relevant_materials', [])}
            
            Provide Socratic guidance following the Harvard 7 Principles.
            """
            
            # Call LLM
            response = await self.llm.acomplete(
                system_prompt + "\n\n" + user_message
            )
            
            response_text = response.text
            
            # Parse response (in production, would be structured JSON)
            return {
                "success": True,
                "guidance": response_text,
                "follow_up_question": "What do you think happens next?",  # TODO: extract from LLM
                "source": concept.get('name', 'Course Material')
            }
        
        except Exception as e:
            self.logger.error(f"Response generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_system_prompt(
        self,
        concept: Dict[str, Any],
        hint_level: int,
        learner_mastery: float
    ) -> str:
        """
        Build system prompt enforcing Harvard 7 Pedagogical Principles.
        
        Args:
            concept: Concept being taught
            hint_level: Appropriate hint level
            learner_mastery: Learner's current mastery
            
        Returns:
            System prompt
        """
        hint_instructions = {
            0: "Encourage them to struggle with the problem. Ask guiding questions.",
            1: "Gently guide their thinking with questions. Don't give answers.",
            2: "Ask clarifying questions to help them think through it.",
            3: "Show a partial example. Let them complete it.",
            4: "Provide fuller explanation but still ask them to apply it.",
            5: "Give direct explanation (last resort - only if absolutely stuck)"
        }
        
        prompt = f"""
You are an expert educator using the Socratic Method and Harvard 7 Pedagogical Principles.

HARVARD 7 PRINCIPLES (ENFORCE ALL):
1. ❌ NEVER give direct answers - guide with questions instead
2. ✅ Keep responses SHORT (2-4 sentences max) - prevent cognitive overload
3. ✅ Reveal ONE STEP AT A TIME - build understanding progressively
4. ✅ Ask "What do YOU think?" BEFORE helping - encourage productive struggle
5. ✅ Praise EFFORT, not intelligence - build growth mindset
6. ✅ Personalized feedback - address THEIR specific error/thinking
7. ✅ Ground ONLY in verified sources - use course materials, not speculation

CURRENT CONTEXT:
- Concept: {concept.get('name', 'Unknown')} (Difficulty: {concept.get('difficulty', 2)}/5)
- Learner's Current Understanding: {learner_mastery:.0%}
- Hint Level: {hint_level}/5 - {hint_instructions[hint_level]}

RESPONSE GUIDELINES:
- KEEP IT SHORT: 2-4 sentences maximum
- NEVER give the answer directly - guide them to think
- Use questions, not statements
- Ask "What do you think...?" or "Can you explain...?"
- Reference the course materials (RAG context provided)
- Praise their effort and thinking process
- If they're struggling, give them a hint (level {hint_level})

Remember: Your goal is NOT to transfer knowledge from you to them,
but to guide THEM to discover understanding themselves.
"""
        
        return prompt
