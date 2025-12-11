import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging
import numpy as np

from backend.core.base_agent import BaseAgent, AgentType
from backend.models import DocumentInput, KnowledgeExtractionOutput, ConceptNode, ConceptRelationship
from backend.prompts import KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT
from llama_index.llms.gemini import Gemini
from backend.config import get_settings

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """7 Relationship Types per Thesis Specification"""
    REQUIRES = "REQUIRES"                      # Prerequisite knowledge
    IS_PREREQUISITE_OF = "IS_PREREQUISITE_OF"  # Reverse dependency
    NEXT = "NEXT"                              # Recommended sequence
    REMEDIATES = "REMEDIATES"                  # Concept that fixes understanding
    HAS_ALTERNATIVE_PATH = "HAS_ALTERNATIVE_PATH"  # Parallel learning option
    SIMILAR_TO = "SIMILAR_TO"                  # Semantic similarity
    IS_SUB_CONCEPT_OF = "IS_SUB_CONCEPT_OF"    # Hierarchical structure


class BloomLevel(str, Enum):
    """Bloom's Taxonomy Levels"""
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"


class KnowledgeExtractionAgent(BaseAgent):
    """
    Knowledge Extraction Agent - Automatically build Course Knowledge Graph from documents.
    
    Features (per Thesis):
    1. SPR Generator - 3-layer extraction (Concept, Relationship, Metadata)
    2. 7 Relationship Types (REQUIRES, IS_PREREQUISITE_OF, NEXT, REMEDIATES, 
       HAS_ALTERNATIVE_PATH, SIMILAR_TO, IS_SUB_CONCEPT_OF)
    3. 3-Way Node Merging Algorithm (Semantic + Structural + Contextual)
    4. Enhanced Metadata (SemanticTags, FocusedSemanticTags, TimeEstimate, Bloom's Level)
    
    Process Flow:
    1. Receive document content
    2. Layer 1: Core Concept Extraction
    3. Layer 2: Relationship Extraction (7 types)
    4. Layer 3: Validation & Metadata
    5. Node Merging (if duplicate concepts)
    6. Create nodes + relationships in Neo4j
    7. Return extraction results
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None):
        super().__init__(agent_id, AgentType.KNOWLEDGE_EXTRACTION, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or Gemini(
            model=self.settings.GEMINI_MODEL,
            api_key=self.settings.GOOGLE_API_KEY
        )
        self.logger = logging.getLogger(f"KnowledgeExtractionAgent.{agent_id}")
        
        # Similarity thresholds for node merging
        self.SEMANTIC_THRESHOLD = 0.85
        self.STRUCTURAL_THRESHOLD = 0.7
        self.CONTEXTUAL_THRESHOLD = 0.6
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Main execution method."""
        try:
            document_content = kwargs.get("document_content")
            document_title = kwargs.get("document_title", "Untitled")
            document_type = kwargs.get("document_type", "LECTURE")
            existing_concepts = kwargs.get("existing_concepts", [])
            
            if not document_content:
                return {
                    "success": False,
                    "error": "document_content is required",
                    "agent_id": self.agent_id
                }
            
            self.logger.info(f"🔍 Extracting knowledge from: {document_title}")
            
            # Step 1: Layer 1 - Core Concept Extraction
            layer1_result = await self._extract_layer1_concepts(
                document_content, document_title
            )
            if not layer1_result["success"]:
                return layer1_result
            
            # Step 2: Layer 2 - Relationship Extraction (7 types)
            layer2_result = await self._extract_layer2_relationships(
                document_content, layer1_result["concepts"]
            )
            if not layer2_result["success"]:
                return layer2_result
            
            # Step 3: Layer 3 - Validation & Enhanced Metadata
            layer3_result = await self._extract_layer3_metadata(
                layer1_result["concepts"]
            )
            if not layer3_result["success"]:
                return layer3_result
            
            enriched_concepts = layer3_result["enriched_concepts"]
            relationships = layer2_result["relationships"]
            
            # Step 4: Node Merging (if existing concepts)
            if existing_concepts:
                merge_result = await self._merge_nodes(
                    enriched_concepts, existing_concepts
                )
                enriched_concepts = merge_result["merged_concepts"]
                self.logger.info(f"Merged {merge_result['merged_count']} duplicate concepts")
            
            # Step 5: Create in Neo4j
            neo4j = self.state_manager.neo4j
            created_concepts = 0
            for concept in enriched_concepts:
                success = await neo4j.create_course_concept(
                    concept_id=concept["concept_id"],
                    name=concept["name"],
                    difficulty=concept["difficulty"],
                    description=concept["description"],
                    bloom_level=concept.get("bloom_level", "UNDERSTAND"),
                    time_estimate=concept.get("time_estimate", 30),
                    semantic_tags=concept.get("semantic_tags", []),
                    focused_tags=concept.get("focused_tags", [])
                )
                if success:
                    created_concepts += 1
            
            # Create relationships (all 7 types)
            created_relationships = 0
            for rel in relationships:
                success = await neo4j.create_relationship(
                    source_id=rel["source_concept_id"],
                    target_id=rel["target_concept_id"],
                    rel_type=rel["relation_type"],
                    confidence=rel.get("confidence", 0.8)
                )
                if success:
                    created_relationships += 1
            
            # Step 6: Save extraction metadata
            document_id = f"doc_{int(datetime.now().timestamp())}"
            await self.save_state(
                f"extraction_{document_id}",
                {
                    "title": document_title,
                    "type": document_type,
                    "concepts_count": len(enriched_concepts),
                    "relationships_count": len(relationships),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            result = {
                "success": True,
                "agent_id": self.agent_id,
                "document_id": document_id,
                "document_title": document_title,
                "concepts_extracted": len(enriched_concepts),
                "concepts_created": created_concepts,
                "relationships_created": created_relationships,
                "relationship_types": list(set(r["relation_type"] for r in relationships)),
                "concepts": enriched_concepts
            }
            
            # Emit event for other agents
            await self.send_message(
                receiver="planner",
                message_type="knowledge_extracted",
                payload={
                    "document_id": document_id,
                    "concepts_count": len(enriched_concepts),
                    "relationship_types": result["relationship_types"]
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
    
    async def _extract_layer1_concepts(
        self, document_content: str, document_title: str
    ) -> Dict[str, Any]:
        """Layer 1: Core Concept Extraction"""
        try:
            prompt = f"""
You are a knowledge extraction expert. Extract all learning concepts from this document.

Document Title: {document_title}

Document Content:
{document_content[:8000]}

For each concept, extract:
1. concept_id: Unique identifier (e.g., "SQL_SELECT", "SQL_JOIN")
2. name: Human-readable name
3. description: 1-2 sentence definition
4. learning_objective: What learner will be able to do
5. examples: 1-2 concrete examples
6. difficulty: 1-5 (1=beginner, 5=expert)

Return ONLY valid JSON array:
[
  {{
    "concept_id": "CONCEPT_NAME",
    "name": "Concept Name",
    "description": "Definition...",
    "learning_objective": "Learner will...",
    "examples": ["Example 1", "Example 2"],
    "difficulty": 2
  }}
]
"""
            response = await self.llm.acomplete(prompt)
            response_text = response.text
            
            # Parse JSON
            json_start = response_text.find("[")
            json_end = response_text.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                concepts = json.loads(response_text[json_start:json_end])
                return {"success": True, "concepts": concepts}
            
            return {"success": False, "error": "Could not parse Layer 1 output"}
        
        except Exception as e:
            self.logger.error(f"Layer 1 extraction error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _extract_layer2_relationships(
        self, document_content: str, concepts: List[Dict]
    ) -> Dict[str, Any]:
        """Layer 2: Relationship Extraction (7 Types)"""
        try:
            concept_names = [c["concept_id"] for c in concepts]
            
            prompt = f"""
You are a curriculum designer. Identify relationships between these concepts.

Concepts: {json.dumps(concept_names)}

Document Context:
{document_content[:4000]}

Relationship Types (use EXACTLY these):
1. REQUIRES - A requires B as prerequisite
2. IS_PREREQUISITE_OF - A is prerequisite of B
3. NEXT - A should be learned before B (sequence)
4. REMEDIATES - Learning A helps fix misunderstanding of B
5. HAS_ALTERNATIVE_PATH - A and B are alternative ways to learn same skill
6. SIMILAR_TO - A and B are semantically similar
7. IS_SUB_CONCEPT_OF - A is a sub-topic of B

Return ONLY valid JSON array:
[
  {{
    "source_concept_id": "CONCEPT_A",
    "target_concept_id": "CONCEPT_B",
    "relation_type": "REQUIRES",
    "confidence": 0.9,
    "reasoning": "Why this relationship exists"
  }}
]
"""
            response = await self.llm.acomplete(prompt)
            response_text = response.text
            
            json_start = response_text.find("[")
            json_end = response_text.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                relationships = json.loads(response_text[json_start:json_end])
                
                # Validate relationship types
                valid_types = [rt.value for rt in RelationshipType]
                validated = [
                    r for r in relationships 
                    if r.get("relation_type") in valid_types
                ]
                
                return {"success": True, "relationships": validated}
            
            return {"success": False, "error": "Could not parse Layer 2 output"}
        
        except Exception as e:
            self.logger.error(f"Layer 2 extraction error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _extract_layer3_metadata(
        self, concepts: List[Dict]
    ) -> Dict[str, Any]:
        """Layer 3: Validation & Enhanced Metadata"""
        try:
            enriched = []
            
            for concept in concepts:
                prompt = f"""
Enrich this learning concept with metadata.

Concept: {json.dumps(concept)}

Generate:
1. semantic_tags: 15-20 related keywords
2. focused_tags: 3-5 most important keywords
3. bloom_level: REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, or CREATE
4. time_estimate: Minutes to learn (10-120)
5. common_misconceptions: 2-3 typical mistakes learners make

Return ONLY valid JSON:
{{
  "semantic_tags": ["tag1", "tag2", ...],
  "focused_tags": ["tag1", "tag2", "tag3"],
  "bloom_level": "UNDERSTAND",
  "time_estimate": 30,
  "common_misconceptions": ["Misconception 1", "Misconception 2"]
}}
"""
                response = await self.llm.acomplete(prompt)
                response_text = response.text
                
                try:
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        metadata = json.loads(response_text[json_start:json_end])
                        enriched_concept = {**concept, **metadata}
                        enriched.append(enriched_concept)
                    else:
                        enriched.append(concept)
                except:
                    enriched.append(concept)
            
            return {"success": True, "enriched_concepts": enriched}
        
        except Exception as e:
            self.logger.error(f"Layer 3 extraction error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _merge_nodes(
        self, new_concepts: List[Dict], existing_concepts: List[Dict]
    ) -> Dict[str, Any]:
        """
        3-Way Node Merging Algorithm
        
        1. Semantic Similarity (Embeddings)
        2. Structural Similarity (Jaccard of prerequisites)  
        3. Contextual Similarity (Jaccard of tags)
        """
        merged_concepts = []
        merged_count = 0
        
        for new_concept in new_concepts:
            best_match = None
            best_score = 0
            
            for existing in existing_concepts:
                # 1. Semantic Similarity (description + examples)
                semantic_sim = self._calculate_text_similarity(
                    new_concept.get("description", ""),
                    existing.get("description", "")
                )
                
                # 2. Structural Similarity (skipped if no graph data)
                structural_sim = 0.0
                
                # 3. Contextual Similarity (tags)
                new_tags = set(new_concept.get("semantic_tags", []))
                existing_tags = set(existing.get("semantic_tags", []))
                contextual_sim = self._jaccard_similarity(new_tags, existing_tags)
                
                # Weighted score
                total_score = (
                    0.5 * semantic_sim +
                    0.2 * structural_sim +
                    0.3 * contextual_sim
                )
                
                if total_score > best_score and total_score > self.SEMANTIC_THRESHOLD:
                    best_score = total_score
                    best_match = existing
            
            if best_match:
                # Merge into existing concept
                merged_concept = self._merge_two_concepts(best_match, new_concept)
                merged_concepts.append(merged_concept)
                merged_count += 1
            else:
                # New unique concept
                merged_concepts.append(new_concept)
        
        return {
            "merged_concepts": merged_concepts,
            "merged_count": merged_count
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity (production would use embeddings)"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        return self._jaccard_similarity(words1, words2)
    
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 and not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _merge_two_concepts(
        self, existing: Dict, new: Dict
    ) -> Dict[str, Any]:
        """Merge two concepts, keeping best data from each"""
        merged = existing.copy()
        
        # Merge examples
        existing_examples = existing.get("examples", [])
        new_examples = new.get("examples", [])
        merged["examples"] = list(set(existing_examples + new_examples))[:5]
        
        # Merge tags
        existing_tags = set(existing.get("semantic_tags", []))
        new_tags = set(new.get("semantic_tags", []))
        merged["semantic_tags"] = list(existing_tags | new_tags)[:20]
        
        # Keep higher difficulty if different
        merged["difficulty"] = max(
            existing.get("difficulty", 2),
            new.get("difficulty", 2)
        )
        
        return merged
