# Entity Resolver for Knowledge Extraction
"""
Entity Resolver: Merge duplicate/similar concepts using 3-way similarity.

Similarity Components:
1. Semantic: Embedding cosine similarity (description/name)
2. Structural: Jaccard similarity of prerequisites/neighbors
3. Contextual: Jaccard similarity of tags

Algorithm:
1. Compute pairwise similarities for new vs existing concepts
2. Cluster similar concepts using agglomerative clustering
3. Select representative for each cluster
4. Remap all relationships to representatives
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EntityMatch:
    """A match between two concepts"""
    new_concept_id: str
    existing_concept_id: str
    semantic_score: float
    structural_score: float
    contextual_score: float
    combined_score: float
    should_merge: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "new_concept_id": self.new_concept_id,
            "existing_concept_id": self.existing_concept_id,
            "semantic_score": round(self.semantic_score, 3),
            "structural_score": round(self.structural_score, 3),
            "contextual_score": round(self.contextual_score, 3),
            "combined_score": round(self.combined_score, 3),
            "should_merge": self.should_merge
        }


@dataclass
class ResolutionResult:
    """Result of entity resolution"""
    resolved_concepts: List[Dict[str, Any]]
    resolved_relationships: List[Dict[str, Any]]
    merge_mapping: Dict[str, str]  # old_id -> representative_id
    matches: List[EntityMatch]
    stats: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "resolved_concept_count": len(self.resolved_concepts),
            "resolved_relationship_count": len(self.resolved_relationships),
            "merges_performed": len(self.merge_mapping),
            "stats": self.stats,
            "matches": [m.to_dict() for m in self.matches]
        }


class EntityResolver:
    """
    Entity Resolver: Merge duplicate concepts.
    
    Implements 3-way similarity as per thesis:
    - Semantic: 50% weight (embedding cosine)
    - Structural: 25% weight (prerequisite overlap)
    - Contextual: 25% weight (tag overlap)
    """
    
    # Similarity weights
    W_SEMANTIC = 0.50
    W_STRUCTURAL = 0.25
    W_CONTEXTUAL = 0.25
    
    # Thresholds
    MERGE_THRESHOLD = 0.85        # Combined score for auto-merge
    HUMAN_REVIEW_THRESHOLD = 0.70 # Suggest for review
    
    def __init__(
        self,
        embedding_model: Optional[Any] = None,
        merge_threshold: float = 0.85,
        use_embeddings: bool = True
    ):
        """
        Initialize Entity Resolver.
        
        Args:
            embedding_model: Sentence transformer model (optional)
            merge_threshold: Similarity threshold for merging
            use_embeddings: Whether to use embeddings for semantic similarity
        """
        self.merge_threshold = merge_threshold
        self.use_embeddings = use_embeddings
        self._embedding_model = embedding_model
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
        # Try to load embedding model
        if use_embeddings and embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded embedding model: all-MiniLM-L6-v2")
            except ImportError:
                logger.warning("sentence-transformers not installed, using text similarity fallback")
                self.use_embeddings = False
    
    def resolve(
        self,
        new_concepts: List[Dict[str, Any]],
        existing_concepts: List[Dict[str, Any]],
        new_relationships: List[Dict[str, Any]],
        existing_relationships: List[Dict[str, Any]]
    ) -> ResolutionResult:
        """
        Resolve entities between new and existing concepts.
        
        Args:
            new_concepts: Newly extracted concepts
            existing_concepts: Concepts already in the KG
            new_relationships: Newly extracted relationships
            existing_relationships: Relationships already in the KG
            
        Returns:
            ResolutionResult with merged concepts and remapped relationships
        """
        logger.info(f"Entity resolution: {len(new_concepts)} new vs {len(existing_concepts)} existing")
        
        # Build indices
        existing_by_id = {c["concept_id"]: c for c in existing_concepts}
        existing_prereqs = self._build_prereq_map(existing_relationships)
        new_prereqs = self._build_prereq_map(new_relationships)
        
        # Find matches
        matches = []
        merge_mapping: Dict[str, str] = {}  # new_id -> existing_id
        
        for new_concept in new_concepts:
            new_id = new_concept.get("concept_id", "")
            
            best_match = None
            best_score = 0.0
            
            for existing_concept in existing_concepts:
                existing_id = existing_concept.get("concept_id", "")
                
                # Calculate 3-way similarity
                match = self._calculate_similarity(
                    new_concept=new_concept,
                    existing_concept=existing_concept,
                    new_prereqs=new_prereqs.get(new_id, set()),
                    existing_prereqs=existing_prereqs.get(existing_id, set())
                )
                
                matches.append(match)
                
                if match.combined_score > best_score:
                    best_score = match.combined_score
                    best_match = match
            
            # Check if should merge
            if best_match and best_match.combined_score >= self.merge_threshold:
                merge_mapping[new_id] = best_match.existing_concept_id
                best_match.should_merge = True
                logger.debug(f"Merging {new_id} -> {best_match.existing_concept_id} (score: {best_score:.2f})")
        
        # Resolve concepts: keep existing, add truly new
        resolved_concepts = list(existing_concepts)
        for new_concept in new_concepts:
            new_id = new_concept.get("concept_id", "")
            if new_id not in merge_mapping:
                # Truly new concept - add it
                resolved_concepts.append(new_concept)
        
        # Resolve relationships: merge duplicates, remap merged concepts
        resolved_relationships = self._resolve_relationships(
            new_relationships=new_relationships,
            existing_relationships=existing_relationships,
            merge_mapping=merge_mapping
        )
        
        stats = {
            "new_concepts": len(new_concepts),
            "existing_concepts": len(existing_concepts),
            "merged_concepts": len(merge_mapping),
            "truly_new_concepts": len(new_concepts) - len(merge_mapping),
            "total_resolved_concepts": len(resolved_concepts),
            "total_resolved_relationships": len(resolved_relationships)
        }
        
        logger.info(f"Resolution complete: {stats['merged_concepts']} merges, {stats['truly_new_concepts']} new")
        
        return ResolutionResult(
            resolved_concepts=resolved_concepts,
            resolved_relationships=resolved_relationships,
            merge_mapping=merge_mapping,
            matches=[m for m in matches if m.should_merge],
            stats=stats
        )
    
    def _calculate_similarity(
        self,
        new_concept: Dict[str, Any],
        existing_concept: Dict[str, Any],
        new_prereqs: Set[str],
        existing_prereqs: Set[str]
    ) -> EntityMatch:
        """Calculate 3-way similarity between concepts"""
        new_id = new_concept.get("concept_id", "")
        existing_id = existing_concept.get("concept_id", "")
        
        # 1. Semantic similarity
        if self.use_embeddings:
            semantic_score = self._embedding_similarity(
                self._get_concept_text(new_concept),
                self._get_concept_text(existing_concept)
            )
        else:
            semantic_score = self._text_similarity(
                self._get_concept_text(new_concept),
                self._get_concept_text(existing_concept)
            )
        
        # 2. Structural similarity (prerequisite overlap)
        structural_score = self._jaccard_similarity(new_prereqs, existing_prereqs)
        
        # 3. Contextual similarity (tag overlap)
        new_tags = set(new_concept.get("semantic_tags", []) or [])
        existing_tags = set(existing_concept.get("semantic_tags", []) or [])
        contextual_score = self._jaccard_similarity(new_tags, existing_tags)
        
        # Combined score
        combined_score = (
            self.W_SEMANTIC * semantic_score +
            self.W_STRUCTURAL * structural_score +
            self.W_CONTEXTUAL * contextual_score
        )
        
        return EntityMatch(
            new_concept_id=new_id,
            existing_concept_id=existing_id,
            semantic_score=semantic_score,
            structural_score=structural_score,
            contextual_score=contextual_score,
            combined_score=combined_score,
            should_merge=False
        )
    
    def _embedding_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between embeddings"""
        if not self._embedding_model:
            return self._text_similarity(text1, text2)
        
        # Get or compute embeddings
        emb1 = self._get_embedding(text1)
        emb2 = self._get_embedding(text2)
        
        # Cosine similarity
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text, with caching"""
        if text in self._embedding_cache:
            return self._embedding_cache[text]
        
        embedding = self._embedding_model.encode(text, convert_to_numpy=True)
        self._embedding_cache[text] = embedding
        return embedding
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Fallback: Jaccard word similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        return self._jaccard_similarity(words1, words2)
    
    def _jaccard_similarity(self, set1: Set, set2: Set) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 and not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _get_concept_text(self, concept: Dict[str, Any]) -> str:
        """Get text representation of concept for similarity"""
        name = concept.get("name", "")
        description = concept.get("description", "")
        learning_objective = concept.get("learning_objective", "")
        
        return f"{name}. {description}. {learning_objective}".strip()
    
    def _build_prereq_map(self, relationships: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """Build map of concept_id -> set of prerequisites"""
        prereq_map: Dict[str, Set[str]] = defaultdict(set)
        
        for rel in relationships:
            rel_type = rel.get("relationship_type", rel.get("type", ""))
            if rel_type == "REQUIRES":
                source = rel.get("source", "")
                target = rel.get("target", "")
                prereq_map[source].add(target)
        
        return prereq_map
    
    def _resolve_relationships(
        self,
        new_relationships: List[Dict[str, Any]],
        existing_relationships: List[Dict[str, Any]],
        merge_mapping: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Resolve relationships, remapping merged concepts"""
        resolved = []
        seen = set()  # Track (source, target, type) to avoid duplicates
        
        # Add existing relationships
        for rel in existing_relationships:
            key = (rel.get("source"), rel.get("target"), rel.get("relationship_type", rel.get("type")))
            if key not in seen:
                resolved.append(rel)
                seen.add(key)
        
        # Add new relationships with remapping
        for rel in new_relationships:
            source = rel.get("source", "")
            target = rel.get("target", "")
            rel_type = rel.get("relationship_type", rel.get("type", ""))
            
            # Remap if concept was merged
            source = merge_mapping.get(source, source)
            target = merge_mapping.get(target, target)
            
            # Skip self-loops
            if source == target:
                continue
            
            key = (source, target, rel_type)
            if key not in seen:
                new_rel = rel.copy()
                new_rel["source"] = source
                new_rel["target"] = target
                resolved.append(new_rel)
                seen.add(key)
        
        return resolved
    
    def find_clusters(
        self,
        concepts: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        threshold: float = 0.80
    ) -> List[List[str]]:
        """
        Find clusters of similar concepts using agglomerative clustering.
        
        For use within a single extraction batch (not new vs existing).
        
        Returns:
            List of clusters, each cluster is a list of concept_ids
        """
        if len(concepts) < 2:
            return [[c["concept_id"]] for c in concepts]
        
        # Build prerequisite map
        prereq_map = self._build_prereq_map(relationships)
        
        # Compute pairwise similarities
        n = len(concepts)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                match = self._calculate_similarity(
                    concepts[i],
                    concepts[j],
                    prereq_map.get(concepts[i]["concept_id"], set()),
                    prereq_map.get(concepts[j]["concept_id"], set())
                )
                similarity_matrix[i][j] = match.combined_score
                similarity_matrix[j][i] = match.combined_score
        
        # Simple agglomerative clustering
        clusters = [[i] for i in range(n)]  # Start with each concept in its own cluster
        
        while len(clusters) > 1:
            # Find most similar pair of clusters
            best_sim = 0
            best_pair = None
            
            for i, c1 in enumerate(clusters):
                for j, c2 in enumerate(clusters[i + 1:], i + 1):
                    # Average linkage
                    sim = np.mean([similarity_matrix[a][b] for a in c1 for b in c2])
                    if sim > best_sim:
                        best_sim = sim
                        best_pair = (i, j)
            
            if best_sim < threshold:
                break  # No more clusters to merge
            
            # Merge clusters
            i, j = best_pair
            new_cluster = clusters[i] + clusters[j]
            clusters = [c for k, c in enumerate(clusters) if k not in (i, j)]
            clusters.append(new_cluster)
        
        # Convert indices to concept_ids
        return [[concepts[i]["concept_id"] for i in cluster] for cluster in clusters]
    
    def select_representative(self, cluster: List[Dict[str, Any]]) -> str:
        """
        Select representative concept from cluster.
        
        Strategy: Prefer concept with longest description (most complete)
        """
        if not cluster:
            return ""
        
        best = max(
            cluster,
            key=lambda c: len(c.get("description", "") or "")
        )
        return best.get("concept_id", "")
