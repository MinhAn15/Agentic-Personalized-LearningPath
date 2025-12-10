import json
from typing import Dict, Any, List
from datetime import datetime
import logging

from backend.core.base_agent import BaseAgent, AgentType
from backend.models import DocumentInput, KnowledgeExtractionOutput, ConceptNode, ConceptRelationship
from backend.prompts import KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT
from llama_index.llms.openai import OpenAI
from backend.config import get_settings

logger = logging.getLogger(__name__)

class KnowledgeExtractionAgent(BaseAgent):
    """
    Knowledge Extraction Agent - Automatically build Course Knowledge Graph from documents.
    
    Responsibility:
    - Parse educational documents
    - Extract key learning concepts
    - Identify prerequisite relationships
    - Create nodes + relationships in Neo4j Course KG
    
    Process Flow:
    1. Receive document content
    2. Call LLM to extract structured concepts
    3. Validate and parse LLM output
    4. Create concept nodes in Neo4j
    5. Create relationships in Neo4j
    6. Return extraction results
    7. Emit event for other agents
    
    Example:
        agent = KnowledgeExtractionAgent(...)
        result = await agent.execute(
            document_content="SQL tutorial...",
            document_title="SQL Basics"
        )
        # Returns: {
        #   "success": True,
        #   "concepts_created": 8,
        #   "relationships_created": 5,
        #   "document_id": "doc_123"
        # }
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        """
        Initialize Knowledge Extraction Agent.
        
        Args:
            agent_id: Unique agent identifier
            state_manager: Central state manager
            event_bus: Event bus for inter-agent communication
            llm: LLM instance (OpenAI by default)
        """
        super().__init__(agent_id, AgentType.KNOWLEDGE_EXTRACTION, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or OpenAI(
            model=self.settings.OPENAI_MODEL,
            api_key=self.settings.OPENAI_API_KEY
        )
        self.logger = logging.getLogger(f"KnowledgeExtractionAgent.{agent_id}")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method.
        
        Args:
            document_content: str - Content of educational document
            document_title: str - Title of document
            document_type: str - Type of document (lecture, tutorial, etc.)
            
        Returns:
            Dict with execution results
        """
        try:
            document_content = kwargs.get("document_content")
            document_title = kwargs.get("document_title", "Untitled")
            document_type = kwargs.get("document_type", "LECTURE")
            
            if not document_content:
                return {
                    "success": False,
                    "error": "document_content is required",
                    "agent_id": self.agent_id
                }
            
            self.logger.info(f"🔍 Extracting knowledge from: {document_title}")
            
            # Step 1: Extract concepts using LLM
            extraction_result = await self._extract_concepts_from_llm(
                document_content,
                document_title
            )
            
            if not extraction_result["success"]:
                return extraction_result
            
            extraction_output = extraction_result["extraction_output"]
            
            # Step 2: Create concept nodes in Neo4j
            neo4j = self.state_manager.neo4j
            created_concepts = 0
            for concept in extraction_output.concepts:
                success = await neo4j.create_course_concept(
                    concept_id=concept.concept_id,
                    name=concept.name,
                    difficulty=concept.difficulty.value,
                    description=concept.description
                )
                if success:
                    created_concepts += 1
            
            # Step 3: Create relationships in Neo4j
            created_relationships = 0
            for rel in extraction_output.relationships:
                success = await neo4j.add_prerequisite(
                    concept_id=rel.source_concept_id,
                    prerequisite_id=rel.target_concept_id
                )
                if success:
                    created_relationships += 1
            
            # Step 4: Save extraction metadata
            await self.save_state(
                f"extraction_{extraction_output.document_id}",
                {
                    "title": document_title,
                    "type": document_type,
                    "concepts_count": len(extraction_output.concepts),
                    "relationships_count": len(extraction_output.relationships),
                    "timestamp": extraction_output.extraction_timestamp.isoformat()
                }
            )
            
            result = {
                "success": True,
                "agent_id": self.agent_id,
                "document_id": extraction_output.document_id,
                "document_title": document_title,
                "concepts_extracted": len(extraction_output.concepts),
                "concepts_created": created_concepts,
                "relationships_created": created_relationships,
                "concepts": [
                    {
                        "concept_id": c.concept_id,
                        "name": c.name,
                        "difficulty": c.difficulty.value
                    }
                    for c in extraction_output.concepts
                ]
            }
            
            # Step 5: Emit event for other agents
            await self.send_message(
                receiver="planner",
                message_type="knowledge_extracted",
                payload={
                    "document_id": extraction_output.document_id,
                    "concepts_count": len(extraction_output.concepts)
                }
            )
            
            self.logger.info(f"✅ Knowledge extraction complete: {created_concepts} concepts, {created_relationships} relationships")
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ Extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    async def _extract_concepts_from_llm(
        self,
        document_content: str,
        document_title: str
    ) -> Dict[str, Any]:
        """
        Call LLM to extract concepts from document.
        
        Args:
            document_content: The document text
            document_title: Title of document
            
        Returns:
            Dict with success flag and extraction output
        """
        try:
            # Prepare prompt for LLM
            user_prompt = f"""
            Document Title: {document_title}
            
            Document Content:
            {document_content}
            
            Extract all key learning concepts from this document.
            Return ONLY valid JSON, no markdown formatting.
            """
            
            # Call LLM
            response = await self.llm.acomplete(
                KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT + "\n\n" + user_prompt
            )
            
            # Parse LLM response
            response_text = response.text
            
            # Extract JSON from response
            try:
                # Try to find JSON in response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    extracted_data = json.loads(json_str)
                else:
                    return {
                        "success": False,
                        "error": "Could not find JSON in LLM response"
                    }
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing error: {e}")
                return {
                    "success": False,
                    "error": f"Invalid JSON from LLM: {e}"
                }
            
            # Build extraction output
            concepts = [
                ConceptNode(
                    concept_id=c["concept_id"],
                    name=c["name"],
                    description=c["description"],
                    difficulty=c["difficulty"],
                    document_source=document_title,
                    tags=c.get("tags", [])
                )
                for c in extracted_data.get("concepts", [])
            ]
            
            relationships = [
                ConceptRelationship(
                    source_concept_id=r["source_concept_id"],
                    target_concept_id=r["target_concept_id"],
                    relation_type=r["relation_type"],
                    confidence=r.get("confidence", 0.8)
                )
                for r in extracted_data.get("relationships", [])
            ]
            
            document_id = f"doc_{int(datetime.now().timestamp())}"
            
            extraction_output = KnowledgeExtractionOutput(
                concepts=concepts,
                relationships=relationships,
                document_id=document_id,
                total_concepts=len(concepts),
                total_relationships=len(relationships)
            )
            
            return {
                "success": True,
                "extraction_output": extraction_output
            }
        
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return {
                "success": False,
                "error": f"LLM error: {e}"
            }
