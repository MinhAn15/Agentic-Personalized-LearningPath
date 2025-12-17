# Domain Taxonomy and NL Mapper
"""
Controlled Vocabulary Domain System with Natural Language Mapping.

Features:
1. 5 canonical domains (mis, bi, de, ds, aie)
2. Alias dictionary for NL matching
3. LLM fallback for ambiguous input (constrained to 5 options)
4. Extensible via admin-only domain additions

Usage:
    mapper = DomainMapper()
    domain = mapper.map("I want to learn SQL for MIS")
    # Returns: DomainMapping(domain_key="mis", confidence=0.95, ...)
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DomainKey(str, Enum):
    """Canonical domain keys (controlled vocabulary)"""
    MIS = "mis"          # Management Information System
    BI = "bi"            # Business Intelligence
    DE = "de"            # Data Engineering
    DS = "ds"            # Data Science
    AIE = "aie"          # AI/ML Engineering


@dataclass
class Domain:
    """Domain definition"""
    key: DomainKey
    name: str
    description: str
    aliases: List[str]
    
    def matches(self, text: str) -> bool:
        """Check if text matches this domain"""
        text_lower = text.lower()
        
        # Check key
        if self.key.value in text_lower:
            return True
        
        # Check aliases
        for alias in self.aliases:
            if alias.lower() in text_lower:
                return True
        
        return False


@dataclass
class DomainMapping:
    """Result of domain mapping"""
    domain_key: str           # Canonical key (mis, bi, de, ds, aie)
    domain_name: str          # Display name
    confidence: float         # 0.0 - 1.0
    matched_alias: str        # Which alias matched
    user_input: str           # Original user input
    needs_confirmation: bool  # If confidence < threshold
    suggestions: List[str]    # Alternative domains if ambiguous
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_key": self.domain_key,
            "domain_name": self.domain_name,
            "confidence": self.confidence,
            "matched_alias": self.matched_alias,
            "needs_confirmation": self.needs_confirmation,
            "suggestions": self.suggestions
        }


# ==========================================
# CANONICAL DOMAIN DEFINITIONS
# ==========================================

DOMAINS: List[Domain] = [
    Domain(
        key=DomainKey.MIS,
        name="Management Information System",
        description="Business systems, enterprise software, ERP, database management for business",
        aliases=[
            "mis", "management information system", "httt", "hệ thống thông tin",
            "enterprise system", "erp", "business system", "information system",
            "khoa httt", "sql for business", "database for business", "mis sql"
        ]
    ),
    Domain(
        key=DomainKey.BI,
        name="Business Intelligence",
        description="Reporting, dashboards, data visualization, business analytics",
        aliases=[
            "bi", "business intelligence", "dashboard", "tableau", "power bi",
            "reporting", "data visualization", "olap", "data warehouse", "dwh",
            "business analytics", "bi dashboard", "analytics reporting"
        ]
    ),
    Domain(
        key=DomainKey.DE,
        name="Data Engineering",
        description="Data pipelines, ETL, data infrastructure, big data systems",
        aliases=[
            "de", "data engineering", "data engineer", "etl", "data pipeline",
            "airflow", "spark", "kafka", "data infrastructure", "big data",
            "data lake", "data warehouse engineer", "batch processing",
            "stream processing", "data platform"
        ]
    ),
    Domain(
        key=DomainKey.DS,
        name="Data Science",
        description="Statistical analysis, machine learning, predictive modeling",
        aliases=[
            "ds", "data science", "data scientist", "machine learning",
            "ml", "statistics", "statistical analysis", "predictive modeling",
            "data analysis", "pandas", "scikit-learn", "sklearn", "regression",
            "classification", "clustering", "khoa học dữ liệu"
        ]
    ),
    Domain(
        key=DomainKey.AIE,
        name="AI Engineering",
        description="Production ML systems, MLOps, deep learning, AI applications",
        aliases=[
            "aie", "ai engineering", "ml engineering", "mlops", "deep learning",
            "neural network", "tensorflow", "pytorch", "llm", "nlp",
            "computer vision", "ai application", "production ml", "ml pipeline",
            "model deployment", "ai/ml", "artificial intelligence"
        ]
    )
]

# Build lookup dictionaries
DOMAIN_BY_KEY: Dict[str, Domain] = {d.key.value: d for d in DOMAINS}
DOMAIN_KEYS: List[str] = [d.key.value for d in DOMAINS]


class DomainMapper:
    """
    Map natural language input to canonical domain.
    
    Hybrid approach:
    1. Exact match on domain key
    2. Alias matching (substring)
    3. Keyword scoring
    4. LLM fallback (constrained to 5 options)
    """
    
    # Confidence threshold for auto-selection
    CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self, llm=None):
        """
        Initialize mapper.
        
        Args:
            llm: Optional LLM for ambiguous cases (constrained output)
        """
        self.llm = llm
        self.domains = DOMAINS
        self._alias_cache: Dict[str, str] = {}  # User input -> domain_key (learned)
    
    def map(self, user_input: str) -> DomainMapping:
        """
        Map user input to canonical domain.
        
        Args:
            user_input: Natural language input (e.g., "SQL cho MIS")
            
        Returns:
            DomainMapping with domain_key and confidence
        """
        if not user_input or not user_input.strip():
            return self._default_mapping(user_input)
        
        text = user_input.strip().lower()
        
        # Check cache first
        if text in self._alias_cache:
            domain = DOMAIN_BY_KEY[self._alias_cache[text]]
            return DomainMapping(
                domain_key=domain.key.value,
                domain_name=domain.name,
                confidence=1.0,
                matched_alias="cached",
                user_input=user_input,
                needs_confirmation=False,
                suggestions=[]
            )
        
        # Score all domains
        scores: List[Tuple[Domain, float, str]] = []
        for domain in self.domains:
            score, matched = self._score_domain(text, domain)
            scores.append((domain, score, matched))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        best_domain, best_score, best_match = scores[0]
        
        # Check if clear winner
        if best_score >= self.CONFIDENCE_THRESHOLD:
            # Auto-select
            return DomainMapping(
                domain_key=best_domain.key.value,
                domain_name=best_domain.name,
                confidence=best_score,
                matched_alias=best_match,
                user_input=user_input,
                needs_confirmation=False,
                suggestions=[]
            )
        elif best_score > 0:
            # Needs confirmation - provide suggestions
            suggestions = [s[0].name for s in scores[:3] if s[1] > 0]
            return DomainMapping(
                domain_key=best_domain.key.value,
                domain_name=best_domain.name,
                confidence=best_score,
                matched_alias=best_match,
                user_input=user_input,
                needs_confirmation=True,
                suggestions=suggestions
            )
        else:
            # No match - return default with all options
            return self._default_mapping(user_input)
    
    def _score_domain(self, text: str, domain: Domain) -> Tuple[float, str]:
        """
        Score how well text matches a domain.
        
        Returns:
            (score, matched_alias)
        """
        # Exact key match
        if domain.key.value == text:
            return 1.0, domain.key.value
        
        # Key in text (e.g., "mis course")
        if domain.key.value in text:
            return 0.9, domain.key.value
        
        # Full name match
        if domain.name.lower() in text:
            return 0.95, domain.name
        
        # Alias matching
        best_alias_score = 0.0
        best_alias = ""
        
        for alias in domain.aliases:
            alias_lower = alias.lower()
            
            if alias_lower == text:
                return 0.95, alias
            
            if alias_lower in text:
                # Longer matches are better
                score = 0.6 + (len(alias_lower) / 50)
                if score > best_alias_score:
                    best_alias_score = min(score, 0.85)
                    best_alias = alias
        
        return best_alias_score, best_alias
    
    def _default_mapping(self, user_input: str) -> DomainMapping:
        """Return default mapping when no match found"""
        return DomainMapping(
            domain_key=DomainKey.MIS.value,  # Default to MIS
            domain_name="Management Information System",
            confidence=0.0,
            matched_alias="",
            user_input=user_input,
            needs_confirmation=True,
            suggestions=[d.name for d in self.domains]
        )
    
    def confirm_mapping(self, user_input: str, domain_key: str) -> bool:
        """
        Confirm and cache a mapping.
        
        Args:
            user_input: Original input
            domain_key: Confirmed domain key
            
        Returns:
            True if cached successfully
        """
        if domain_key not in DOMAIN_KEYS:
            return False
        
        self._alias_cache[user_input.strip().lower()] = domain_key
        return True
    
    def get_domain(self, domain_key: str) -> Optional[Domain]:
        """Get domain by key"""
        return DOMAIN_BY_KEY.get(domain_key)
    
    def list_domains(self) -> List[Dict[str, str]]:
        """List all available domains"""
        return [
            {"key": d.key.value, "name": d.name, "description": d.description}
            for d in self.domains
        ]
    
    def is_valid_domain_key(self, key: str) -> bool:
        """Check if key is valid"""
        return key in DOMAIN_KEYS


# ==========================================
# LLM-BASED MAPPING (CONSTRAINED OUTPUT)
# ==========================================

DOMAIN_MAPPING_PROMPT = """
You are mapping user input to one of 5 learning domains.

Available domains:
1. mis - Management Information System (business systems, ERP, SQL for business)
2. bi - Business Intelligence (dashboards, reporting, data visualization)
3. de - Data Engineering (ETL, pipelines, Spark, data infrastructure)
4. ds - Data Science (statistics, ML, predictive modeling)
5. aie - AI Engineering (production ML, deep learning, MLOps)

User input: {user_input}

Return ONLY the domain key (mis, bi, de, ds, or aie) that best matches this input.
If uncertain, return the closest match - do NOT invent new domains.

Domain key:
"""


async def map_domain_with_llm(
    user_input: str,
    llm
) -> DomainMapping:
    """
    Use LLM to map input to domain (constrained to 5 options).
    
    This is used when alias matching fails or confidence is low.
    """
    prompt = DOMAIN_MAPPING_PROMPT.format(user_input=user_input)
    
    try:
        response = await llm.acomplete(prompt)
        domain_key = response.text.strip().lower()
        
        # Validate - must be one of 5 keys
        if domain_key not in DOMAIN_KEYS:
            # Try to extract key from response
            for key in DOMAIN_KEYS:
                if key in domain_key:
                    domain_key = key
                    break
            else:
                domain_key = "mis"  # Default
        
        domain = DOMAIN_BY_KEY[domain_key]
        
        return DomainMapping(
            domain_key=domain_key,
            domain_name=domain.name,
            confidence=0.7,  # LLM mapping = moderate confidence
            matched_alias="llm",
            user_input=user_input,
            needs_confirmation=True,  # Always confirm LLM mapping
            suggestions=[domain.name]
        )
    
    except Exception as e:
        # Fallback to default
        return DomainMapping(
            domain_key="mis",
            domain_name="Management Information System",
            confidence=0.0,
            matched_alias="fallback",
            user_input=user_input,
            needs_confirmation=True,
            suggestions=[d.name for d in DOMAINS]
        )


# ==========================================
# SINGLETON INSTANCE
# ==========================================

_domain_mapper: Optional[DomainMapper] = None


def get_domain_mapper() -> DomainMapper:
    """Get singleton DomainMapper instance"""
    global _domain_mapper
    if _domain_mapper is None:
        _domain_mapper = DomainMapper()
    return _domain_mapper
