"""
3-Layer Grounding Manager for Tutor Agent.

Per THESIS Section 3.5.x:
- Layer 1: Document RAG (Chroma) - 40% weight
- Layer 2: Course KG (Neo4j) - 35% weight
- Layer 3: Personal KG (Neo4j) - 25% weight

Purpose: Prevent hallucination by grounding responses in verified knowledge.
Target: Reduce hallucination rate from 14.2% to 3.1%
"""

import logging
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GroundingContext:
    """Container for 3-layer grounding data"""
    
    # Layer 1: Document RAG
    layer1_doc: Dict = field(default_factory=lambda: {
        'chunks': [],
        'relevance_score': 0.0
    })
    
    # Layer 2: Course KG
    layer2_kg: Dict = field(default_factory=lambda: {
        'definition': '',
        'examples': [],
        'misconceptions': [],
        'prerequisites': []
    })
    
    # Layer 3: Personal KG
    layer3_personal: Dict = field(default_factory=lambda: {
        'mastery_level': 0.0,
        'past_errors': [],
        'learning_style': 'VISUAL'
    })
    
    overall_confidence: float = 0.0
    
    def get_combined_context(self) -> str:
        """Get formatted context for LLM prompt"""
        context_parts = []
        
        if self.layer2_kg.get('definition'):
            context_parts.append(f"Definition: {self.layer2_kg['definition']}")
        
        if self.layer2_kg.get('examples'):
            examples = self.layer2_kg['examples'][:2]
            context_parts.append(f"Examples: {', '.join(str(e) for e in examples)}")
        
        if self.layer1_doc.get('chunks'):
            chunks = self.layer1_doc['chunks'][:2]
            context_parts.append(f"Reference material: {' '.join(chunks)}")
        
        if self.layer3_personal.get('past_errors'):
            errors = self.layer3_personal['past_errors']
            context_parts.append(f"Learner's past errors: {', '.join(errors)}")
        
        return '\n'.join(context_parts)


class GroundingManager:
    """
    3-Layer Grounding with confidence-based fallback.
    
    Weights (per THESIS):
    - Document RAG: 40%
    - Course KG: 35%
    - Personal KG: 25%
    
    Confidence thresholds:
    - >= 0.8: Confident response
    - >= 0.5: Response with citation
    - >= 0.3: Suggest prerequisite review
    - < 0.3: Suggest review materials together
    """
    
    # Grounding weights
    W_DOC = 0.40
    W_KG = 0.35
    W_PERSONAL = 0.25
    
    # Confidence thresholds
    THRESHOLD_HIGH = 0.8
    THRESHOLD_MEDIUM = 0.5
    THRESHOLD_LOW = 0.3
    
    def __init__(self, chroma_client=None, neo4j_driver=None, embedding_model=None):
        """
        Initialize grounding manager.
        
        Args:
            chroma_client: ChromaDB client for document RAG
            neo4j_driver: Neo4j driver for KG queries
            embedding_model: Sentence transformer for embeddings
        """
        self.chroma = chroma_client
        self.neo4j = neo4j_driver
        self.embeddings = embedding_model
        self.logger = logging.getLogger(f"{__name__}.GroundingManager")
    
    async def ground_context(
        self, 
        concept_id: str, 
        learner_id: str, 
        user_query: str
    ) -> Tuple[GroundingContext, bool]:
        """
        Retrieve grounding context from all 3 layers.
        
        Returns:
            (GroundingContext, is_grounded) tuple
        """
        context = GroundingContext()
        
        # Layer 1: Document RAG (40%)
        l1_score = await self._retrieve_document_context(concept_id, user_query, context)
        
        # Layer 2: Course KG (35%)
        l2_score = await self._retrieve_course_kg_context(concept_id, context)
        
        # Layer 3: Personal KG (25%)
        l3_score = await self._retrieve_personal_kg_context(learner_id, concept_id, context)
        
        # Calculate overall confidence
        context.overall_confidence = (
            self.W_DOC * l1_score + 
            self.W_KG * l2_score + 
            self.W_PERSONAL * l3_score
        )
        
        is_grounded = context.overall_confidence >= self.THRESHOLD_MEDIUM
        
        self.logger.info(f"Grounding: L1={l1_score:.2f}, L2={l2_score:.2f}, L3={l3_score:.2f}, "
                        f"Overall={context.overall_confidence:.2f}, Grounded={is_grounded}")
        
        return context, is_grounded
    
    async def _retrieve_document_context(
        self, 
        concept_id: str, 
        user_query: str, 
        context: GroundingContext
    ) -> float:
        """Layer 1: Retrieve from Chroma document store"""
        try:
            if not self.chroma or not self.embeddings:
                return 0.0
            
            # Create query embedding
            query = f"{concept_id}: {user_query}"
            embedding = self.embeddings.encode(query)
            
            # Query Chroma
            results = self.chroma.query(
                query_embeddings=[embedding.tolist()],
                n_results=3,
                collection_name="course_materials"
            )
            
            if results and results.get('documents'):
                context.layer1_doc['chunks'] = results['documents'][0] if results['documents'] else []
                
                # Convert distance to relevance score
                if results.get('distances') and results['distances'][0]:
                    distance = results['distances'][0][0]
                    relevance = 1.0 / (1.0 + distance)
                    context.layer1_doc['relevance_score'] = relevance
                    return relevance
            
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Error retrieving document context: {e}")
            return 0.0
    
    async def _retrieve_course_kg_context(
        self, 
        concept_id: str, 
        context: GroundingContext
    ) -> float:
        """Layer 2: Retrieve from Course KG (Neo4j)"""
        try:
            if not self.neo4j:
                return 0.0
            
            query = """
            MATCH (c:CourseConcept {concept_id: $id})
            OPTIONAL MATCH (c)-[:REQUIRES]->(p)
            RETURN c.definition as definition, 
                   c.examples as examples, 
                   c.commonerrors as misconceptions,
                   collect(p.concept_id) as prerequisites
            """
            
            async with self.neo4j.session() as session:
                result = await session.run(query, id=concept_id)
                record = await result.single()
            
            if record:
                context.layer2_kg['definition'] = record['definition'] or ''
                context.layer2_kg['examples'] = record['examples'] or []
                context.layer2_kg['misconceptions'] = record['misconceptions'] or []
                context.layer2_kg['prerequisites'] = record['prerequisites'] or []
                
                # Score based on data completeness
                fields_filled = sum([
                    bool(record['definition']),
                    bool(record['examples']),
                    bool(record['misconceptions'])
                ])
                return fields_filled / 3.0
            
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Error retrieving Course KG context: {e}")
            return 0.0
    
    async def _retrieve_personal_kg_context(
        self, 
        learner_id: str, 
        concept_id: str, 
        context: GroundingContext
    ) -> float:
        """Layer 3: Retrieve from Personal KG (Neo4j)"""
        try:
            if not self.neo4j:
                return 0.0
            
            query = """
            MATCH (l:Learner {learner_id: $lid})
            OPTIONAL MATCH (l)-[:HAS_MASTERY]->(m:MasteryNode {concept_id: $cid})
            OPTIONAL MATCH (l)-[:HAS_ERROR]->(e:ErrorEpisode)-[:RELATED_TO]->(c:CourseConcept {concept_id: $cid})
            RETURN m.level as mastery_level, 
                   collect(e.misconception_type) as errors
            """
            
            async with self.neo4j.session() as session:
                result = await session.run(query, lid=learner_id, cid=concept_id)
                record = await result.single()
            
            if record:
                context.layer3_personal['mastery_level'] = record['mastery_level'] or 0.0
                context.layer3_personal['past_errors'] = [e for e in record['errors'] if e]
                
                # Score: has mastery data OR has error history
                has_data = bool(record['mastery_level']) or len(record['errors']) > 0
                return 1.0 if has_data else 0.0
            
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Error retrieving Personal KG context: {e}")
            return 0.0
    
    def get_confidence_response_prefix(self, confidence: float) -> str:
        """Get appropriate response prefix based on confidence level"""
        if confidence >= self.THRESHOLD_HIGH:
            return ""  # No prefix needed
        elif confidence >= self.THRESHOLD_MEDIUM:
            return "[Based on course materials] "
        elif confidence >= self.THRESHOLD_LOW:
            return "I'm not fully confident here. Let's review the fundamentals first. "
        else:
            return "Let me suggest we review some materials together before proceeding. "
