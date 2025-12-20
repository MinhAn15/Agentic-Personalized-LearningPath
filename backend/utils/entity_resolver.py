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
    
    # Similarity weights (Scientifically balanced for Pedagogical Graphs)
    W_SEMANTIC = 0.60    # Core meaning (Embedding)
    W_STRUCTURAL = 0.30  # Position in graph (Prereqs)
    W_CONTEXTUAL = 0.10  # Metadata overlap (Tags)
    
    # Thresholds
    MERGE_THRESHOLD = 0.85        # Combined score for auto-merge
    HUMAN_REVIEW_THRESHOLD = 0.70 # Suggest for review
    
    # Scalability: Two-Stage Resolution Parameters
    TOP_K_CANDIDATES = 20         # Max candidates to retrieve per concept
    
    def __init__(
        self,
        embedding_model: Optional[Any] = None,
        merge_threshold: float = 0.85,
        use_embeddings: bool = True
    ):
        """
        Initialize Entity Resolver.
        
        Args:
            embedding_model: LlamaIndex/Gemini-compatible embedding model
            merge_threshold: Similarity threshold for merging
            use_embeddings: Whether to use embeddings for semantic similarity
        """
        self.merge_threshold = merge_threshold
        self.use_embeddings = use_embeddings
        self._embedding_model = embedding_model
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
        if use_embeddings and embedding_model is None:
            logger.warning("No embedding model provided. Semantic similarity will fallback to Jaccard.")
            self.use_embeddings = False
    
    def resolve(
        self,
        new_concepts: List[Dict[str, Any]],
        existing_concepts: List[Dict[str, Any]],
        new_relationships: List[Dict[str, Any]],
        existing_relationships: List[Dict[str, Any]]
    ) -> ResolutionResult:
        """
        Unified resolution: 
        1. Resolve duplicates WITHIN the new concepts (Internal Clustering)
        2. Resolve duplicates vs EXISTING concepts (External Merging)
        """
        logger.info(f"Entity resolution: {len(new_concepts)} new vs {len(existing_concepts)} existing")
        
        # --- Step 1: Internal Clustering (New vs New) ---
        # Find clusters within the new batch to avoid redundant comparisons
        internal_clusters = self.find_clusters(new_concepts, new_relationships)
        
        unique_new_concepts = []
        internal_mapping = {} # old_id -> representative_id
        
        for cluster_ids in internal_clusters:
            cluster_objs = [c for c in new_concepts if c["concept_id"] in cluster_ids]
            rep_id = self.select_representative(cluster_objs)
            rep_obj = next(c for c in cluster_objs if c["concept_id"] == rep_id)
            
            unique_new_concepts.append(rep_obj)
            for cid in cluster_ids:
                internal_mapping[cid] = rep_id

        # Remap relationships within the unique batch
        unique_new_relationships = self._resolve_relationships(
            new_relationships=new_relationships,
            existing_relationships=[],
            merge_mapping=internal_mapping
        )

        # --- Step 2: External Merging (Two-Stage: Candidate Retrieval + Deep Comparison) ---
        existing_by_id = {c["concept_id"]: c for c in existing_concepts}
        existing_prereqs = self._build_prereq_map(existing_relationships)
        new_prereqs = self._build_prereq_map(unique_new_relationships)
        
        # Pre-compute embeddings for existing concepts (cached)
        existing_embeddings = {}
        if self.use_embeddings and existing_concepts:
            logger.info(f"Pre-computing embeddings for {len(existing_concepts)} existing concepts...")
            for c in existing_concepts:
                text = self._get_concept_text(c)
                existing_embeddings[c["concept_id"]] = self._get_embedding(text)
        
        matches = []
        external_mapping: Dict[str, str] = {}  # unique_new_id -> existing_id
        
        for new_concept in unique_new_concepts:
            new_id = new_concept.get("concept_id", "")
            
            # STAGE 1: Candidate Retrieval (Vector Similarity Top-K)
            candidates = self._retrieve_candidates(
                new_concept=new_concept,
                existing_concepts=existing_concepts,
                existing_embeddings=existing_embeddings,
                top_k=self.TOP_K_CANDIDATES
            )
            
            if not candidates:
                continue  # No similar candidates found
            
            # STAGE 2: Deep Comparison (3-Way Scoring on Top-K only)
            best_match = None
            best_score = 0.0
            
            for existing_concept in candidates:
                existing_id = existing_concept.get("concept_id", "")
                
                match = self._calculate_similarity(
                    new_concept=new_concept,
                    existing_concept=existing_concept,
                    new_prereqs=new_prereqs.get(new_id, set()),
                    existing_prereqs=existing_prereqs.get(existing_id, set())
                )
                
                if match.combined_score > best_score:
                    best_score = match.combined_score
                    best_match = match
            
            if best_match and best_match.combined_score >= self.merge_threshold:
                # MARK FOR MERGE
                external_mapping[new_id] = best_match.existing_concept_id
                best_match.should_merge = True
                matches.append(best_match)
                
                # CONFLICT RESOLUTION: Update the existing concept's attributes
                target_concept = next(c for c in existing_concepts if c["concept_id"] == best_match.existing_concept_id)
                merged_attributes = self._resolve_attribute_conflicts(target_concept, new_concept)
                target_concept.update(merged_attributes)
                logger.debug(f"Merged attributes for {best_match.existing_concept_id} using Weighted Average")
        
        # --- Step 3: Final Consolidation ---
        # truly_unique = concepts that aren't merged into existing
        final_concepts = list(existing_concepts)
        truly_new_concepts = []
        for new_concept in unique_new_concepts:
            new_id = new_concept.get("concept_id", "")
            if new_id not in external_mapping:
                final_concepts.append(new_concept)
                truly_new_concepts.append(new_concept)
        
        # Combine mappings: raw_new_id -> representative_new_id -> existing_id
        full_merge_mapping = {}
        for raw_id, rep_id in internal_mapping.items():
            final_target = external_mapping.get(rep_id, rep_id)
            if final_target != raw_id:
                full_merge_mapping[raw_id] = final_target

        resolved_relationships = self._resolve_relationships(
            new_relationships=new_relationships,
            existing_relationships=existing_relationships,
            merge_mapping=full_merge_mapping
        )
        
        stats = {
            "raw_new_concepts": len(new_concepts),
            "internal_unique_concepts": len(unique_new_concepts),
            "existing_concepts": len(existing_concepts),
            "merged_to_existing": len(external_mapping),
            "truly_new_concepts": len(truly_new_concepts),
            "total_resolved_concepts": len(final_concepts),
            "total_resolved_relationships": len(resolved_relationships)
        }
        
        logger.info(f"Resolution complete: {stats['internal_unique_concepts']} unique from {stats['raw_new_concepts']} raw")
        
        return ResolutionResult(
            resolved_concepts=final_concepts,
            resolved_relationships=resolved_relationships,
            merge_mapping=full_merge_mapping,
            matches=matches,
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
        
        # Support LlamaIndex embedding model interface
        if hasattr(self._embedding_model, "get_text_embedding"):
            embedding = self._embedding_model.get_text_embedding(text)
            embedding_np = np.array(embedding)
        # Support SentenceTransformer interface
        elif hasattr(self._embedding_model, "encode"):
            embedding_np = self._embedding_model.encode(text, convert_to_numpy=True)
        else:
            logger.warning("Unknown embedding model interface")
            return np.zeros(1)
            
        self._embedding_cache[text] = embedding_np
        return embedding_np
    
    def _retrieve_candidates(
        self,
        new_concept: Dict[str, Any],
        existing_concepts: List[Dict[str, Any]],
        existing_embeddings: Dict[str, np.ndarray],
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Two-Stage Entity Resolution: Stage 1 - Candidate Retrieval.
        
        Uses vector similarity to quickly find Top-K most similar existing concepts
        before performing expensive 3-way deep comparison.
        
        Complexity: O(M) where M = number of existing concepts
        vs O(M * feature_comparisons) for full comparison
        
        Args:
            new_concept: The new concept to find matches for
            existing_concepts: All concepts in the KG
            existing_embeddings: Pre-computed embeddings for existing concepts
            top_k: Maximum number of candidates to return
            
        Returns:
            List of top-K most similar existing concepts
        """
        if not existing_concepts:
            return []
        
        # Get embedding for new concept
        new_text = self._get_concept_text(new_concept)
        new_embedding = self._get_embedding(new_text)
        
        # Calculate cosine similarities with all existing concepts
        similarities = []
        for existing_concept in existing_concepts:
            existing_id = existing_concept.get("concept_id", "")
            
            # Use pre-computed embedding if available
            if existing_id in existing_embeddings:
                existing_embedding = existing_embeddings[existing_id]
            else:
                existing_text = self._get_concept_text(existing_concept)
                existing_embedding = self._get_embedding(existing_text)
            
            # Quick cosine similarity calculation
            dot_product = np.dot(new_embedding, existing_embedding)
            norm1 = np.linalg.norm(new_embedding)
            norm2 = np.linalg.norm(existing_embedding)
            
            if norm1 > 0 and norm2 > 0:
                sim = float(dot_product / (norm1 * norm2))
            else:
                sim = 0.0
            
            similarities.append((existing_concept, sim))
        
        # Sort by similarity (descending) and take top-K
        similarities.sort(key=lambda x: x[1], reverse=True)
        candidates = [concept for concept, sim in similarities[:top_k]]
        
        logger.debug(f"Retrieved {len(candidates)} candidates for '{new_concept.get('name', 'unknown')}'")
        return candidates
    
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
        Select representative concept from cluster and MERGE attributes.
        
        Strategy: 
        1. Select Rep: One with longest description (most complete info)
        2. Merge Attributes: Use Weighted Average for Difficulty/Time based on confidence (if available)
        """
        if not cluster:
            return ""
        
        # 1. Select initial representative
        best_concept = max(
            cluster,
            key=lambda c: len(c.get("description", "") or "")
        )
        rep_id = best_concept.get("concept_id", "")
        
        # 2. Merge attributes (Weighted Conflict Resolution)
        # We start with the representative's attributes and merge others into it
        merged_attributes = best_concept.copy()
        
        # Collect all values from cluster members
        difficulties = []
        times = []
        
        for member in cluster:
            # Assume default confidence 0.5 if not present (legacy support)
            conf = float(member.get("confidence", 0.5))
            
            if "difficulty" in member and member["difficulty"]:
                try:
                    difficulties.append((float(member["difficulty"]), conf))
                except (ValueError, TypeError):
                    pass
            
            if "time_estimate" in member and member["time_estimate"]:
                try:
                    times.append((float(member["time_estimate"]), conf))
                except (ValueError, TypeError):
                    pass
            
            # Merge set-based attributes (Tags)
            if member["concept_id"] != rep_id:
                current_semantic = set(merged_attributes.get("semantic_tags", []) or [])
                member_semantic = set(member.get("semantic_tags", []) or [])
                merged_attributes["semantic_tags"] = list(current_semantic | member_semantic)
                
                current_focused = set(merged_attributes.get("focused_tags", []) or [])
                member_focused = set(member.get("focused_tags", []) or [])
                merged_attributes["focused_tags"] = list(current_focused | member_focused)

        # Apply Weighted Average Conflict Resolution
        if len(difficulties) > 1:
            merged_attributes["difficulty"] = self._weighted_average(difficulties)
            logger.debug(f"Resolved difficulty conflict for {rep_id}: {merged_attributes['difficulty']:.2f} (from {len(difficulties)} sources)")
            
        if len(times) > 1:
            merged_attributes["time_estimate"] = int(self._weighted_average(times))
            logger.debug(f"Resolved time conflict for {rep_id}: {merged_attributes['time_estimate']}m (from {len(times)} sources)")

        # Update the original object in the list
        best_concept.update(merged_attributes)
        
        return rep_id

    def _resolve_attribute_conflicts(
        self, 
        target_concept: Dict[str, Any], 
        source_concept: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge attributes from source -> target using Weighted Average Strategy.
        Used during External Merging (New vs Existing).
        """
        merged = target_concept.copy()
        
        # Default confidences
        # Existing DB concepts imply higher confidence (e.g., 1.0) or stored confidence
        target_conf = float(target_concept.get("confidence", 1.0)) 
        source_conf = float(source_concept.get("confidence", 0.7)) # New extraction confidence
        
        # Resolve Difficulty
        d1 = target_concept.get("difficulty")
        d2 = source_concept.get("difficulty")
        if d1 is not None and d2 is not None:
            try:
                merged["difficulty"] = self._weighted_average([(float(d1), target_conf), (float(d2), source_conf)])
            except (ValueError, TypeError):
                pass
        
        # Resolve Time Estimate
        t1 = target_concept.get("time_estimate")
        t2 = source_concept.get("time_estimate")
        if t1 is not None and t2 is not None:
            try:
                merged["time_estimate"] = int(self._weighted_average([(float(t1), target_conf), (float(t2), source_conf)]))
            except (ValueError, TypeError):
                pass
            
        # Merge Tags (Union)
        for tag_field in ["semantic_tags", "focused_tags"]:
            s1 = set(target_concept.get(tag_field, []) or [])
            s2 = set(source_concept.get(tag_field, []) or [])
            merged[tag_field] = list(s1 | s2)
            
        return merged

    def _weighted_average(self, values: List[Tuple[float, float]]) -> float:
        """
        Calculate weighted average.
        Args: values: List of (value, weight) tuples
        """
        total_weight = sum(w for v, w in values)
        if total_weight == 0:
            return sum(v for v, w in values) / len(values)
        
        weighted_sum = sum(v * w for v, w in values)
        return weighted_sum / total_weight
