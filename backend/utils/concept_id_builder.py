# Concept ID Builder Utility
"""
Dual-Layer ID System for Course Concepts.

Layer 1: concept_uuid - Internal GUID, immutable
Layer 2: concept_code - Stable business key, human-readable

Pattern: {domain}.{context}.{sanitized_concept}
Example: sql.query.select, stats.descriptive.mean

Benefits:
- concept_uuid: Stable references from Personal KG
- concept_code: Human-readable for debugging, domain-aware to prevent collision
"""

import re
import uuid
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ConceptIdentifiers:
    """
    Dual-layer concept identifiers + SPR snapshot format.
    
    Layers:
    1. concept_uuid: Internal GUID (immutable, for Personal KG refs)
    2. concept_code: Business key {domain}.{context}.{sanitized}
    3. snapshot_node_id: SPR format {NodeLabel}_{SanitizedConcept} for snapshot layer
    """
    concept_uuid: str           # UUIDv4 internal key
    concept_code: str           # {domain}.{context}.{sanitized}
    sanitized_concept: str      # snake_case concept name
    context: str                # topic/domain context
    domain: str                 # course/subject domain
    
    # SPR snapshot layer format
    snapshot_node_id: str = ""  # {NodeLabel}_{SanitizedConcept} for doc overwrite
    
    # Original LLM output (for debugging)
    raw_name: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "concept_uuid": self.concept_uuid,
            "concept_code": self.concept_code,
            "snapshot_node_id": self.snapshot_node_id,
            "sanitized_concept": self.sanitized_concept,
            "context": self.context,
            "domain": self.domain,
            "raw_name": self.raw_name
        }


class ConceptIdBuilder:
    """
    Build concept_code from LLM-extracted raw fields.
    
    LLM provides:
    - name: Human-readable name
    - context: Topic context (e.g., "database queries")
    
    Backend builds:
    - sanitized_concept: snake_case version of name
    - concept_code: {domain}.{sanitized}
    - concept_uuid: UUIDv4
    """
    
    # Characters allowed in sanitized names
    ALLOWED_CHARS = re.compile(r'[^a-z0-9_]')
    
    def __init__(self, default_domain: str = "course"):
        """
        Initialize builder.
        
        Args:
            default_domain: Default domain if not specified
        """
        self.default_domain = default_domain
    
    def build(
        self,
        name: str,
        context: Optional[str] = None,
        domain: Optional[str] = None,
        existing_uuid: Optional[str] = None
    ) -> ConceptIdentifiers:
        """
        Build concept identifiers from LLM raw output.
        
        Args:
            name: Human-readable concept name (e.g., "SELECT Statement")
            context: Topic context (stored in metadata, NOT in ID for stability)
            domain: Course/subject domain (e.g., "sql", "python")
            existing_uuid: If merging with existing concept, keep their UUID
            
        Returns:
            ConceptIdentifiers with all ID layers
        """
        # Sanitize concept name
        sanitized = self._sanitize(name)
        
        # Sanitize context (or default to "concept")
        context_clean = self._sanitize(context) if context else "concept"
        
        # Use provided domain or default
        domain_clean = self._sanitize(domain) if domain else self.default_domain
        
        # FIX Gap 4: ID Stability
        # Use 2-part ID: {domain}.{name} to avoid duplicates when context varies
        # Old: {domain}.{context}.{name} -> Unstable
        concept_code = f"{domain_clean}.{sanitized}"
        
        # Generate or reuse UUID
        concept_uuid = existing_uuid or str(uuid.uuid4())
        
        # Generate SPR snapshot_node_id
        snapshot_node_id = self.generate_spr_node_id("concept", sanitized)
        
        return ConceptIdentifiers(
            concept_uuid=concept_uuid,
            concept_code=concept_code,
            snapshot_node_id=snapshot_node_id,
            sanitized_concept=sanitized,
            context=context_clean,
            domain=domain_clean,
            raw_name=name
        )
    
    def build_from_llm_output(
        self,
        llm_concept: Dict[str, Any],
        domain: Optional[str] = None
    ) -> ConceptIdentifiers:
        """
        Build from LLM extraction output.
        
        Expected LLM output format:
        {
            "name": "SELECT Statement",
            "context": "SQL Queries",
            "description": "..."
        }
        """
        name = llm_concept.get("name", "")
        context = llm_concept.get("context", llm_concept.get("topic", ""))
        
        return self.build(
            name=name,
            context=context,
            domain=domain
        )
    
    def parse_concept_code(self, concept_code: str) -> Tuple[str, str, str]:
        """
        Parse concept_code back into components.
        
        Args:
            concept_code: e.g., "sql.query.select"
            
        Returns:
            Tuple of (domain, context, sanitized_concept)
        """
        parts = concept_code.split(".")
        if len(parts) >= 3:
            return parts[0], parts[1], ".".join(parts[2:])
        elif len(parts) == 2:
            return self.default_domain, parts[0], parts[1]
        else:
            return self.default_domain, "concept", parts[0]
    
    def _sanitize(self, text: str) -> str:
        """
        Sanitize text to snake_case.
        
        "SELECT Statement" -> "select_statement"
        "SQL-JOIN" -> "sql_join"
        """
        if not text:
            return ""
        
        # Lowercase
        result = text.lower()
        
        # Replace common separators with underscore
        result = result.replace("-", "_").replace(" ", "_")
        
        # Remove disallowed characters
        result = self.ALLOWED_CHARS.sub("", result)
        
        # Collapse multiple underscores
        result = re.sub(r'_+', '_', result)
        
        # Strip leading/trailing underscores
        result = result.strip("_")
        
        return result
    
    def generate_spr_node_id(self, node_label: str, sanitized_concept: str) -> str:
        """
        Generate SPR-compliant NodeID for snapshot layer.
        
        Format: {NodeLabel}_{SanitizedConcept}
        Example: concept_select_statement
        
        This is used ONLY in snapshot layer for SPR CSV compatibility.
        """
        label = self._sanitize(node_label) or "concept"
        return f"{label}_{sanitized_concept}"
    
    def is_valid_concept_code(self, concept_code: str) -> bool:
        """Check if concept_code follows the pattern"""
        parts = concept_code.split(".")
        if len(parts) < 2:
            return False
        
        # Each part should be non-empty and lowercase with underscores
        for part in parts:
            if not part or not re.match(r'^[a-z][a-z0-9_]*$', part):
                return False
        
        return True


# Singleton instance for convenience
_default_builder = None


def get_concept_id_builder(domain: str = "course") -> ConceptIdBuilder:
    """Get or create concept ID builder"""
    global _default_builder
    if _default_builder is None or _default_builder.default_domain != domain:
        _default_builder = ConceptIdBuilder(domain)
    return _default_builder
