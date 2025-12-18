# KG Validator for Knowledge Extraction
"""
KG Validator: Validate extracted concepts and relationships before commit.

Validation Rules:
1. Unique node IDs
2. Valid relationship references (source/target exist)
3. Required fields present
4. Enum values valid
5. No self-loops
6. No orphan nodes
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple, DefaultDict
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(str, Enum):
    """Severity of validation issue"""
    ERROR = "ERROR"      # Must fix before commit
    WARNING = "WARNING"  # Should fix, can proceed
    INFO = "INFO"        # Informational


@dataclass
class ValidationIssue:
    """A single validation issue"""
    rule: str
    severity: ValidationSeverity
    message: str
    node_id: Optional[str] = None
    relationship_id: Optional[str] = None
    field: Optional[str] = None
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "severity": self.severity.value,
            "message": self.message,
            "node_id": self.node_id,
            "relationship_id": self.relationship_id,
            "field": self.field,
            "suggested_fix": self.suggested_fix
        }


@dataclass
class ValidationResult:
    """Result of validation"""
    is_valid: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    
    # Stats
    total_nodes: int = 0
    total_relationships: int = 0
    valid_nodes: int = 0
    valid_relationships: int = 0
    
    def add_issue(self, issue: ValidationIssue):
        if issue.severity == ValidationSeverity.ERROR:
            self.errors.append(issue)
            self.is_valid = False
        elif issue.severity == ValidationSeverity.WARNING:
            self.warnings.append(issue)
        else:
            self.info.append(issue)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_nodes": self.total_nodes,
            "total_relationships": self.total_relationships,
            "valid_nodes": self.valid_nodes,
            "valid_relationships": self.valid_relationships,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "info": [i.to_dict() for i in self.info]
        }


class KGValidator:
    """
    Knowledge Graph Validator.
    
    Validates:
    - Node schema (required fields, valid enums)
    - Relationship integrity (source/target exist)
    - Graph structure (no self-loops, orphans)
    """
    
    # Required fields for CourseConcept
    REQUIRED_NODE_FIELDS = ["concept_id", "name"]
    OPTIONAL_NODE_FIELDS = ["description", "difficulty", "bloom_level", "semantic_tags", "examples"]
    
    # Valid enum values
    VALID_BLOOM_LEVELS = ["REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"]
    VALID_RELATIONSHIP_TYPES = [
        "REQUIRES", "IS_PREREQUISITE_OF", "NEXT", "REMEDIATES",
        "HAS_ALTERNATIVE_PATH", "SIMILAR_TO", "IS_SUB_CONCEPT_OF"
    ]
    
    # ID format pattern
    ID_PATTERN = re.compile(r'^[A-Z0-9_]+$')
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, warnings become errors
        """
        self.strict_mode = strict_mode
    
    def validate(
        self,
        nodes: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate nodes and relationships.
        
        Args:
            nodes: List of concept dictionaries
            relationships: List of relationship dictionaries
            
        Returns:
            ValidationResult with issues
        """
        result = ValidationResult(
            is_valid=True,
            total_nodes=len(nodes),
            total_relationships=len(relationships)
        )
        
        # Build node ID set for reference checking
        node_ids: Set[str] = set()
        
        # Validate nodes
        for node in nodes:
            node_issues = self._validate_node(node, node_ids)
            for issue in node_issues:
                result.add_issue(issue)
            
            if not any(i.severity == ValidationSeverity.ERROR for i in node_issues):
                result.valid_nodes += 1
                node_ids.add(node.get("concept_id", ""))
        
        # Validate relationships
        for rel in relationships:
            rel_issues = self._validate_relationship(rel, node_ids)
            for issue in rel_issues:
                result.add_issue(issue)
            
            if not any(i.severity == ValidationSeverity.ERROR for i in rel_issues):
                result.valid_relationships += 1
        
        # Check for orphan nodes
        referenced_nodes = self._get_referenced_nodes(relationships)
        orphan_issues = self._check_orphans(node_ids, referenced_nodes)
        for issue in orphan_issues:
            result.add_issue(issue)
        
        # Check for cycles (DAG enforcement)
        cycle_issues = self._detect_cycles(relationships)
        for issue in cycle_issues:
            result.add_issue(issue)
        
        return result
    
    def _validate_node(self, node: Dict[str, Any], existing_ids: Set[str]) -> List[ValidationIssue]:
        """Validate a single node"""
        issues = []
        concept_id = node.get("concept_id", "")
        
        # Rule 1: Required fields
        for field in self.REQUIRED_NODE_FIELDS:
            if not node.get(field):
                issues.append(ValidationIssue(
                    rule="REQUIRED_FIELD",
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing required field: {field}",
                    node_id=concept_id,
                    field=field,
                    suggested_fix=f"Add '{field}' to node"
                ))
        
        # Rule 2: ID format
        if concept_id and not self.ID_PATTERN.match(concept_id):
            issues.append(ValidationIssue(
                rule="ID_FORMAT",
                severity=ValidationSeverity.WARNING if not self.strict_mode else ValidationSeverity.ERROR,
                message=f"ID '{concept_id}' should be uppercase with underscores",
                node_id=concept_id,
                field="concept_id",
                suggested_fix=concept_id.upper().replace(" ", "_").replace("-", "_")
            ))
        
        # Rule 3: Unique ID
        if concept_id in existing_ids:
            issues.append(ValidationIssue(
                rule="UNIQUE_ID",
                severity=ValidationSeverity.ERROR,
                message=f"Duplicate concept ID: {concept_id}",
                node_id=concept_id,
                field="concept_id",
                suggested_fix=f"{concept_id}_2"
            ))
        
        # Rule 4: Valid bloom_level
        bloom = node.get("bloom_level")
        if bloom and bloom.upper() not in self.VALID_BLOOM_LEVELS:
            issues.append(ValidationIssue(
                rule="VALID_ENUM",
                severity=ValidationSeverity.WARNING,
                message=f"Invalid bloom_level: {bloom}",
                node_id=concept_id,
                field="bloom_level",
                suggested_fix="UNDERSTAND"
            ))
        
        # Rule 5: Difficulty range
        difficulty = node.get("difficulty")
        if difficulty is not None:
            try:
                diff_val = int(difficulty)
                if not 1 <= diff_val <= 5:
                    issues.append(ValidationIssue(
                        rule="VALID_RANGE",
                        severity=ValidationSeverity.WARNING,
                        message=f"Difficulty {diff_val} out of range [1-5]",
                        node_id=concept_id,
                        field="difficulty",
                        suggested_fix="3"
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    rule="VALID_TYPE",
                    severity=ValidationSeverity.WARNING,
                    message=f"Difficulty should be integer, got: {type(difficulty).__name__}",
                    node_id=concept_id,
                    field="difficulty",
                    suggested_fix="2"
                ))
        
        # Rule 6: Description length
        description = node.get("description", "")
        if len(description) < 10:
            issues.append(ValidationIssue(
                rule="MIN_LENGTH",
                severity=ValidationSeverity.WARNING,
                message=f"Description too short ({len(description)} chars)",
                node_id=concept_id,
                field="description"
            ))
        
        return issues
    
    def _validate_relationship(
        self, 
        rel: Dict[str, Any], 
        node_ids: Set[str]
    ) -> List[ValidationIssue]:
        """
        Validate a single relationship including SPR spec fields.
        
        SPR Spec Fields:
        - weight: 0.0-1.0
        - dependency: STRONG, MODERATE, WEAK
        """
        issues = []
        source = rel.get("source", "")
        target = rel.get("target", "")
        rel_type = rel.get("relationship_type", rel.get("type", ""))
        rel_id = f"{source}->{target}"
        
        # Rule 1: Source exists
        if source not in node_ids:
            issues.append(ValidationIssue(
                rule="REF_EXISTS",
                severity=ValidationSeverity.ERROR,
                message=f"Source node not found: {source}",
                relationship_id=rel_id,
                field="source"
            ))
        
        # Rule 2: Target exists
        if target not in node_ids:
            issues.append(ValidationIssue(
                rule="REF_EXISTS",
                severity=ValidationSeverity.ERROR,
                message=f"Target node not found: {target}",
                relationship_id=rel_id,
                field="target"
            ))
        
        # Rule 3: No self-loops
        if source == target:
            issues.append(ValidationIssue(
                rule="NO_SELF_LOOP",
                severity=ValidationSeverity.ERROR,
                message=f"Self-loop detected: {source}",
                relationship_id=rel_id
            ))
        
        # Rule 4: Valid relationship type
        if rel_type and rel_type.upper() not in self.VALID_RELATIONSHIP_TYPES:
            issues.append(ValidationIssue(
                rule="VALID_REL_TYPE",
                severity=ValidationSeverity.WARNING,
                message=f"Unknown relationship type: {rel_type}",
                relationship_id=rel_id,
                field="relationship_type",
                suggested_fix="REQUIRES"
            ))
        
        # Rule 5: Weight range (SPR spec)
        weight = rel.get("weight")
        if weight is not None:
            try:
                w = float(weight)
                if not 0.0 <= w <= 1.0:
                    issues.append(ValidationIssue(
                        rule="VALID_RANGE",
                        severity=ValidationSeverity.WARNING,
                        message=f"Weight {w} out of range [0.0-1.0]",
                        relationship_id=rel_id,
                        field="weight",
                        suggested_fix="0.8"
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    rule="VALID_TYPE",
                    severity=ValidationSeverity.WARNING,
                    message=f"Weight should be float, got: {type(weight).__name__}",
                    relationship_id=rel_id,
                    field="weight",
                    suggested_fix="0.8"
                ))
        
        # Rule 6: Valid dependency (SPR spec)
        dependency = rel.get("dependency")
        if dependency is not None:
            valid_deps = ["STRONG", "MODERATE", "WEAK"]
            if str(dependency).upper() not in valid_deps:
                issues.append(ValidationIssue(
                    rule="VALID_ENUM",
                    severity=ValidationSeverity.WARNING,
                    message=f"Invalid dependency: {dependency}",
                    relationship_id=rel_id,
                    field="dependency",
                    suggested_fix="MODERATE"
                ))
        
        # Rule 7: Confidence range
        confidence = rel.get("confidence")
        if confidence is not None:
            try:
                c = float(confidence)
                if not 0.0 <= c <= 1.0:
                    issues.append(ValidationIssue(
                        rule="VALID_RANGE",
                        severity=ValidationSeverity.WARNING,
                        message=f"Confidence {c} out of range [0.0-1.0]",
                        relationship_id=rel_id,
                        field="confidence",
                        suggested_fix="0.8"
                    ))
            except (ValueError, TypeError):
                pass  # Confidence is optional
        
        return issues
    
    def _get_referenced_nodes(self, relationships: List[Dict[str, Any]]) -> Set[str]:
        """Get set of all nodes referenced in relationships"""
        referenced = set()
        for rel in relationships:
            referenced.add(rel.get("source", ""))
            referenced.add(rel.get("target", ""))
        return referenced
    
    def _check_orphans(
        self, 
        all_nodes: Set[str], 
        referenced_nodes: Set[str]
    ) -> List[ValidationIssue]:
        """Check for orphan nodes (not connected to anything)"""
        issues = []
        orphans = all_nodes - referenced_nodes
        
        # Exclude if only 1 node (can't have relationships)
        if len(all_nodes) <= 1:
            return issues
        
        for orphan in orphans:
            issues.append(ValidationIssue(
                rule="NO_ORPHAN",
                severity=ValidationSeverity.WARNING,
                message=f"Orphan node (no relationships): {orphan}",
                node_id=orphan
            ))
        
        return issues
    
    def auto_fix(
        self, 
        nodes: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]],
        result: ValidationResult
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Attempt to auto-fix issues.
        
        Returns:
            Fixed nodes and relationships
        """
        fixed_nodes = []
        fixed_rels = []
        
        # Fix nodes
        for node in nodes:
            fixed = node.copy()
            
            # Fix ID format
            if fixed.get("concept_id"):
                fixed["concept_id"] = fixed["concept_id"].upper().replace(" ", "_").replace("-", "_")
            
            # Fix bloom_level
            if fixed.get("bloom_level") and fixed["bloom_level"].upper() not in self.VALID_BLOOM_LEVELS:
                fixed["bloom_level"] = "UNDERSTAND"
            
            # Clamp difficulty
            if fixed.get("difficulty"):
                try:
                    fixed["difficulty"] = max(1, min(5, int(fixed["difficulty"])))
                except:
                    fixed["difficulty"] = 2
            
            fixed_nodes.append(fixed)
        
        # Fix relationships
        valid_ids = {n.get("concept_id") for n in fixed_nodes}
        for rel in relationships:
            source = rel.get("source", "").upper().replace(" ", "_")
            target = rel.get("target", "").upper().replace(" ", "_")
            
            # Skip invalid references
            if source not in valid_ids or target not in valid_ids:
                continue
            
            # Skip self-loops
            if source == target:
                continue
            
            fixed = rel.copy()
            fixed["source"] = source
            fixed["target"] = target
            
            # Fix relationship type
            if fixed.get("relationship_type"):
                fixed["relationship_type"] = fixed["relationship_type"].upper()
                if fixed["relationship_type"] not in self.VALID_RELATIONSHIP_TYPES:
                    fixed["relationship_type"] = "REQUIRES"
            
            fixed_rels.append(fixed)
        
        return fixed_nodes, fixed_rels

    def _detect_cycles(self, relationships: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """
        Detect cycles in the relationship graph (DAG enforcement).
        Using persistent DFS.
        """
        issues = []
        adj = defaultdict(list)
        
        # Build adjacency list from input relationships
        for rel in relationships:
            src = rel.get("source")
            tgt = rel.get("target")
            rel_type = rel.get("relationship_type", "")
            
            # Only consider structural relationships for cycles
            if src and tgt and rel_type in ["REQUIRES", "NEXT", "IS_SUB_CONCEPT_OF"]:
                adj[src].append((tgt, rel))
        
        visited = set()
        recursion_stack = set()
        
        def dfs(u, path):
            visited.add(u)
            recursion_stack.add(u)
            path.append(u)
            
            if u in adj:
                for v, rel_data in adj[u]:
                    if v not in visited:
                        if dfs(v, path):
                            return True
                    elif v in recursion_stack:
                        # Cycle detected
                        cycle_path = " -> ".join(path[path.index(v):] + [v])
                        issues.append(ValidationIssue(
                            rule="DAG_VIOLATION",
                            severity=ValidationSeverity.ERROR,
                            message=f"Cycle detected: {cycle_path}",
                            relationship_id=f"{u}->{v}",
                            suggested_fix="Remove one of the relationships in the cycle"
                        ))
                        return True
            
            recursion_stack.remove(u)
            path.pop()
            return False

        # Run DFS from each node
        nodes = list(adj.keys())
        for node in nodes:
            if node not in visited:
                dfs(node, [])
        
        return issues
