"""
Domain Configuration for Knowledge Extraction Agent.

This module implements the Global Theme / Domain Context pattern from LightRAG (Guo et al., 2024).

Scientific Basis:
- LightRAG (2024): Dual-level retrieval uses "global themes" to help LLM understand context
- Prompt Engineering: Domain context constrains output, reduces hallucination
- Knowledge Graph: Domain as root node for entity organization

Usage:
- Admin selects domain when uploading document (REQUIRED)
- Domain is injected into ALL prompts (Chunking, Layer 1-3)
- Domain is for LLM guidance only, NOT for filtering (concepts can be cross-domain)
"""

from typing import List, Optional, Set
from dataclasses import dataclass, field
import json
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class DomainInfo:
    """Information about a learning domain."""
    code: str  # Lowercase, no spaces (e.g., "sql", "machine_learning")
    display_name: str  # Human-readable (e.g., "SQL", "Machine Learning")
    description: str  # Brief description for Admin reference
    keywords: List[str] = field(default_factory=list)  # Related keywords for auto-suggest
    
    def __post_init__(self):
        # Ensure code is lowercase and sanitized
        self.code = self.code.lower().replace(" ", "_").replace("-", "_")


# =============================================================================
# PREDEFINED DOMAINS
# Admin can add new domains, but these are the initial set
# =============================================================================

PREDEFINED_DOMAINS: List[DomainInfo] = [
    # Programming Languages
    DomainInfo(
        code="sql",
        display_name="SQL",
        description="Structured Query Language for database operations",
        keywords=["database", "query", "select", "join", "mysql", "postgresql", "oracle"]
    ),
    DomainInfo(
        code="python",
        display_name="Python",
        description="Python programming language",
        keywords=["programming", "scripting", "django", "flask", "pandas", "numpy"]
    ),
    DomainInfo(
        code="javascript",
        display_name="JavaScript",
        description="JavaScript/TypeScript for web development",
        keywords=["web", "frontend", "react", "vue", "node", "typescript"]
    ),
    
    # Data Science & AI
    DomainInfo(
        code="machine_learning",
        display_name="Machine Learning",
        description="Machine Learning algorithms and techniques",
        keywords=["ml", "ai", "model", "training", "sklearn", "tensorflow", "pytorch"]
    ),
    DomainInfo(
        code="data_science",
        display_name="Data Science",
        description="Data analysis, visualization, and statistics",
        keywords=["analytics", "visualization", "statistics", "pandas", "matplotlib"]
    ),
    DomainInfo(
        code="deep_learning",
        display_name="Deep Learning",
        description="Neural networks and deep learning",
        keywords=["neural", "cnn", "rnn", "transformer", "llm", "gpt"]
    ),
    
    # Databases & Infrastructure
    DomainInfo(
        code="database",
        display_name="Database Systems",
        description="Database design, management, and optimization",
        keywords=["rdbms", "nosql", "indexing", "normalization", "transaction"]
    ),
    DomainInfo(
        code="cloud",
        display_name="Cloud Computing",
        description="AWS, Azure, GCP cloud services",
        keywords=["aws", "azure", "gcp", "serverless", "docker", "kubernetes"]
    ),
    
    # Business & Analytics
    DomainInfo(
        code="bi",
        display_name="Business Intelligence",
        description="BI tools, dashboards, and reporting",
        keywords=["powerbi", "tableau", "reporting", "dashboard", "etl", "data warehouse"]
    ),
    
    # Algorithms & CS Fundamentals
    DomainInfo(
        code="algorithms",
        display_name="Algorithms",
        description="Data structures and algorithms",
        keywords=["sorting", "searching", "graph", "dynamic programming", "complexity"]
    ),
    DomainInfo(
        code="software_engineering",
        display_name="Software Engineering",
        description="Design patterns, architecture, and best practices",
        keywords=["design patterns", "solid", "architecture", "testing", "agile"]
    ),
]


class DomainRegistry:
    """
    Registry for managing learning domains.
    
    Supports:
    - Predefined domains (from PREDEFINED_DOMAINS)
    - Custom domains (added by Admin at runtime)
    - Persistence to JSON file
    """
    
    def __init__(self, custom_domains_file: Optional[str] = None):
        """
        Initialize domain registry.
        
        Args:
            custom_domains_file: Optional path to JSON file for persisting custom domains.
                                If None, uses default path in config directory.
        """
        self._domains: dict[str, DomainInfo] = {}
        self._custom_file = custom_domains_file
        
        # Load predefined domains
        for domain in PREDEFINED_DOMAINS:
            self._domains[domain.code] = domain
        
        # Load custom domains from file (if exists)
        self._load_custom_domains()
    
    def _get_custom_file_path(self) -> str:
        """Get path to custom domains file."""
        if self._custom_file:
            return self._custom_file
        # Default: same directory as this file
        return os.path.join(os.path.dirname(__file__), "custom_domains.json")
    
    def _load_custom_domains(self):
        """Load custom domains from JSON file."""
        filepath = self._get_custom_file_path()
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    custom_list = json.load(f)
                for item in custom_list:
                    domain = DomainInfo(**item)
                    self._domains[domain.code] = domain
                logger.info(f"Loaded {len(custom_list)} custom domains from {filepath}")
            except Exception as e:
                logger.warning(f"Failed to load custom domains: {e}")
    
    def _save_custom_domains(self):
        """Save custom domains to JSON file."""
        filepath = self._get_custom_file_path()
        # Only save domains that are NOT in predefined list
        predefined_codes = {d.code for d in PREDEFINED_DOMAINS}
        custom = [
            {"code": d.code, "display_name": d.display_name, 
             "description": d.description, "keywords": d.keywords}
            for d in self._domains.values() if d.code not in predefined_codes
        ]
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(custom, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(custom)} custom domains to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save custom domains: {e}")
    
    def get_all_domains(self) -> List[DomainInfo]:
        """Get all domains (predefined + custom), sorted by display_name."""
        return sorted(self._domains.values(), key=lambda d: d.display_name)
    
    def get_domain_codes(self) -> List[str]:
        """Get list of all domain codes."""
        return sorted(self._domains.keys())
    
    def get_domain(self, code: str) -> Optional[DomainInfo]:
        """Get domain by code."""
        return self._domains.get(code.lower())
    
    def is_valid_domain(self, code: str) -> bool:
        """Check if domain code is valid."""
        return code.lower() in self._domains
    
    def add_custom_domain(
        self,
        code: str,
        display_name: str,
        description: str = "",
        keywords: List[str] = None
    ) -> DomainInfo:
        """
        Add a new custom domain.
        
        This allows Admin to add new domains at runtime if the predefined
        list doesn't include their subject area.
        
        Args:
            code: Domain code (will be sanitized to lowercase_with_underscores)
            display_name: Human-readable name
            description: Brief description
            keywords: Related keywords for auto-suggest
            
        Returns:
            Created DomainInfo object
            
        Raises:
            ValueError: If domain code already exists
        """
        # Sanitize code
        code = code.lower().replace(" ", "_").replace("-", "_")
        
        if code in self._domains:
            raise ValueError(f"Domain '{code}' already exists")
        
        domain = DomainInfo(
            code=code,
            display_name=display_name,
            description=description,
            keywords=keywords or []
        )
        self._domains[code] = domain
        
        # Persist to file
        self._save_custom_domains()
        
        logger.info(f"Added custom domain: {code} ({display_name})")
        return domain
    
    def suggest_domain(self, text: str) -> Optional[DomainInfo]:
        """
        Suggest a domain based on text content.
        
        Uses keyword matching to suggest the most relevant domain.
        This is for auto-suggestion only, Admin makes final decision.
        """
        text_lower = text.lower()
        best_match = None
        best_score = 0
        
        for domain in self._domains.values():
            score = 0
            # Check domain code in text
            if domain.code in text_lower:
                score += 10
            # Check display name
            if domain.display_name.lower() in text_lower:
                score += 8
            # Check keywords
            for keyword in domain.keywords:
                if keyword.lower() in text_lower:
                    score += 2
            
            if score > best_score:
                best_score = score
                best_match = domain
        
        return best_match if best_score >= 2 else None


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_domain_registry: Optional[DomainRegistry] = None


def get_domain_registry() -> DomainRegistry:
    """Get the global domain registry singleton."""
    global _domain_registry
    if _domain_registry is None:
        _domain_registry = DomainRegistry()
    return _domain_registry


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_domain_list() -> List[str]:
    """Get list of all valid domain codes."""
    return get_domain_registry().get_domain_codes()


def validate_domain(code: str) -> bool:
    """Check if domain code is valid."""
    return get_domain_registry().is_valid_domain(code)


def add_new_domain(code: str, display_name: str, description: str = "") -> DomainInfo:
    """Add a new custom domain (convenience function)."""
    return get_domain_registry().add_custom_domain(code, display_name, description)
