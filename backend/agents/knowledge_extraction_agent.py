"""
Knowledge Extraction Agent

Responsible for:
- Extracting concepts, topics, and entities from educational content
- Building knowledge graph nodes and relationships
- Identifying prerequisites and dependencies between concepts
- Working with LlamaIndex for document processing
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from backend.core.base_agent import BaseAgent, AgentType, AgentMessage
from backend.core.event_bus import EventType, Event

logger = logging.getLogger(__name__)


class KnowledgeNode:
    """Represents a knowledge concept/node in the graph"""
    
    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: str,  # concept, topic, skill, prerequisite
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self.description = description
        self.metadata = metadata or {}
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "node_type": self.node_type,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class KnowledgeRelationship:
    """Represents a relationship between two knowledge nodes"""
    
    def __init__(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,  # prerequisite, related_to, part_of, leads_to
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.relationship_type = relationship_type
        self.weight = weight
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type,
            "weight": self.weight,
            "metadata": self.metadata
        }


class KnowledgeExtractionAgent(BaseAgent):
    """
    Agent responsible for extracting knowledge from educational content.
    
    Uses LlamaIndex for:
    - Document loading and parsing
    - Text chunking and embedding
    - Entity and concept extraction via LLM
    
    Outputs:
    - Knowledge nodes (concepts, topics, skills)
    - Relationships (prerequisites, dependencies)
    - Metadata (difficulty, time estimates)
    """
    
    def __init__(
        self,
        agent_id: str,
        state_manager: Any,
        event_bus: Any,
        llm: Optional[Any] = None,  # LlamaIndex LLM
        embed_model: Optional[Any] = None  # Embedding model
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.KNOWLEDGE_EXTRACTION,
            state_manager=state_manager,
            event_bus=event_bus
        )
        self.llm = llm
        self.embed_model = embed_model
        
        # Subscribe to relevant events
        self.event_bus.subscribe(
            EventType.KNOWLEDGE_EXTRACTED,
            self._on_knowledge_event
        )
    
    async def execute(
        self,
        content: str,
        content_type: str = "text",
        source_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract knowledge from content.
        
        Args:
            content: The text content to analyze
            content_type: Type of content (text, pdf, url)
            source_id: Optional identifier for the source
            
        Returns:
            Dict containing extracted nodes and relationships
        """
        self.logger.info(f"🔍 Starting knowledge extraction from {content_type}")
        
        try:
            # Step 1: Preprocess content
            processed_content = await self._preprocess_content(content, content_type)
            
            # Step 2: Extract concepts
            nodes = await self._extract_concepts(processed_content)
            
            # Step 3: Identify relationships
            relationships = await self._identify_relationships(nodes, processed_content)
            
            # Step 4: Enrich with metadata
            enriched_nodes = await self._enrich_nodes(nodes)
            
            # Step 5: Save to state
            result = {
                "status": "success",
                "source_id": source_id,
                "nodes": [node.to_dict() for node in enriched_nodes],
                "relationships": [rel.to_dict() for rel in relationships],
                "metadata": {
                    "extracted_at": datetime.now().isoformat(),
                    "node_count": len(enriched_nodes),
                    "relationship_count": len(relationships)
                }
            }
            
            await self.save_state("last_extraction", result)
            
            # Step 6: Publish event
            await self.event_bus.publish(Event(
                event_type=EventType.KNOWLEDGE_EXTRACTED,
                source=self.agent_id,
                payload=result
            ))
            
            self.logger.info(
                f"✅ Extracted {len(nodes)} concepts, "
                f"{len(relationships)} relationships"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "nodes": [],
                "relationships": []
            }
    
    async def _preprocess_content(
        self, 
        content: str, 
        content_type: str
    ) -> str:
        """Preprocess and clean content"""
        # For now, basic cleaning
        # TODO: Add LlamaIndex document loaders for PDF, HTML, etc.
        processed = content.strip()
        self.logger.debug(f"📄 Preprocessed content: {len(processed)} chars")
        return processed
    
    async def _extract_concepts(self, content: str) -> List[KnowledgeNode]:
        """Extract concepts from content using LLM"""
        nodes = []
        
        if self.llm is None:
            # Mock extraction for testing without LLM
            self.logger.warning("⚠️ No LLM configured, using mock extraction")
            nodes = self._mock_extract_concepts(content)
        else:
            # TODO: Real LLM extraction
            # Use LlamaIndex to extract entities and concepts
            pass
        
        return nodes
    
    def _mock_extract_concepts(self, content: str) -> List[KnowledgeNode]:
        """Mock concept extraction for testing"""
        # Simple keyword-based mock extraction
        import hashlib
        
        mock_concepts = [
            ("Machine Learning", "concept", "Core AI/ML concept"),
            ("Neural Networks", "topic", "Deep learning architecture"),
            ("Python Programming", "skill", "Programming language for ML"),
        ]
        
        nodes = []
        for name, node_type, desc in mock_concepts:
            node_id = hashlib.md5(name.encode()).hexdigest()[:8]
            nodes.append(KnowledgeNode(
                node_id=node_id,
                name=name,
                node_type=node_type,
                description=desc
            ))
        
        return nodes
    
    async def _identify_relationships(
        self, 
        nodes: List[KnowledgeNode],
        content: str
    ) -> List[KnowledgeRelationship]:
        """Identify relationships between concepts"""
        relationships = []
        
        if len(nodes) < 2:
            return relationships
        
        # Mock: Create prerequisite chain
        for i in range(len(nodes) - 1):
            relationships.append(KnowledgeRelationship(
                source_id=nodes[i].node_id,
                target_id=nodes[i + 1].node_id,
                relationship_type="prerequisite",
                weight=0.8
            ))
        
        return relationships
    
    async def _enrich_nodes(
        self, 
        nodes: List[KnowledgeNode]
    ) -> List[KnowledgeNode]:
        """Enrich nodes with additional metadata"""
        for node in nodes:
            # Add difficulty estimation
            node.metadata["difficulty"] = "intermediate"
            # Add estimated learning time
            node.metadata["estimated_hours"] = 2.0
            # Add bloom's taxonomy level
            node.metadata["bloom_level"] = "understand"
        
        return nodes
    
    async def _on_knowledge_event(self, event: Event) -> None:
        """Handle knowledge-related events"""
        if event.source != self.agent_id:
            self.logger.debug(f"📥 Received knowledge event from {event.source}")
    
    async def extract_from_document(
        self, 
        document_path: str
    ) -> Dict[str, Any]:
        """Extract knowledge from a document file"""
        # TODO: Implement with LlamaIndex document loaders
        self.logger.info(f"📁 Loading document: {document_path}")
        
        # Placeholder - would use:
        # from llama_index.core import SimpleDirectoryReader
        # documents = SimpleDirectoryReader(input_files=[document_path]).load_data()
        
        return await self.execute(
            content="[Document content would be loaded here]",
            content_type="document",
            source_id=document_path
        )
    
    async def extract_from_url(self, url: str) -> Dict[str, Any]:
        """Extract knowledge from a URL"""
        self.logger.info(f"🌐 Loading URL: {url}")
        
        # TODO: Implement with LlamaIndex web reader
        return await self.execute(
            content="[URL content would be loaded here]",
            content_type="url",
            source_id=url
        )
