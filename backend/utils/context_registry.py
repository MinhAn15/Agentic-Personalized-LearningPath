# Context Registry for Knowledge Graph
"""
Context Registry: Gradual normalization of LLM-extracted contexts.

Strategy (per proposal):
- V1: LLM extracts context freely (document-specific)
- V2: System normalizes via registry (context_raw → context_key)
- V3: UI can suggest contexts from registry

Storage:
- context_raw: Original LLM extraction (snake_case)
- context_key: Normalized key from registry (nullable initially)

This allows flexible extraction while enabling gradual standardization.
"""

import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ContextStatus(str, Enum):
    """Status for context entries in registry"""
    ACTIVE = "active"           # Approved, ready for use
    PENDING = "pending"         # Awaiting admin review
    REJECTED = "rejected"       # Admin rejected, not promoted
    DEPRECATED = "deprecated"   # Replaced by another context_key


@dataclass
class PendingContext:
    """
    Tracking for unmapped context_raw awaiting admin review.
    
    Trigger Rules (per proposal):
    - freq_7d >= 5 (used often in last 7 days)
    - freq_7d >= 2 AND >= 2 documents (cross-document pattern)
    
    SLA: Batch review every Friday, top 20-50 by freq_7d.
    """
    context_raw: str
    domain_key: str
    frequency: int = 0                  # Total occurrences (all time)
    freq_7d: int = 0                    # Occurrences in last 7 days
    document_ids: Set[str] = None       # Unique documents containing this
    first_seen: str = ""
    last_seen: str = ""
    
    # Timestamp list for 7-day rolling window
    usage_timestamps: List[str] = None
    
    def __post_init__(self):
        if self.document_ids is None:
            self.document_ids = set()
        if self.usage_timestamps is None:
            self.usage_timestamps = []
        if not self.first_seen:
            self.first_seen = datetime.now().isoformat()
        self.last_seen = datetime.now().isoformat()
    
    def record_usage(self, document_id: str = None):
        """Record a usage of this context"""
        now = datetime.now()
        self.frequency += 1
        self.last_seen = now.isoformat()
        self.usage_timestamps.append(now.isoformat())
        
        if document_id:
            self.document_ids.add(document_id)
        
        # Recompute 7-day frequency
        self._compute_freq_7d()
    
    def _compute_freq_7d(self):
        """Compute frequency in last 7 days"""
        now = datetime.now()
        cutoff = now - timedelta(days=7)
        
        valid_timestamps = []
        for ts in self.usage_timestamps:
            try:
                dt = datetime.fromisoformat(ts)
                if dt >= cutoff:
                    valid_timestamps.append(ts)
            except:
                pass
        
        self.usage_timestamps = valid_timestamps  # Prune old timestamps
        self.freq_7d = len(valid_timestamps)
    
    def needs_review(self) -> bool:
        """
        Check if this context should be queued for admin review.
        
        Triggers (per proposal defaults):
        - freq_7d >= 5 (used often in last 7 days)
        - freq_7d >= 2 AND >= 2 documents (cross-document pattern)
        """
        self._compute_freq_7d()  # Ensure up-to-date
        
        if self.freq_7d >= 5:
            return True
        if self.freq_7d >= 2 and len(self.document_ids) >= 2:
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        self._compute_freq_7d()
        return {
            "context_raw": self.context_raw,
            "domain_key": self.domain_key,
            "frequency": self.frequency,
            "freq_7d": self.freq_7d,
            "document_count": len(self.document_ids),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "needs_review": self.needs_review()
        }


@dataclass
class ContextEntry:
    """Registry entry for a normalized context"""
    context_key: str          # Canonical key (snake_case)
    display_name: str         # Human-readable name
    domain_key: str           # Which domain this belongs to
    aliases: List[str]        # Variations that map to this key
    status: ContextStatus = ContextStatus.ACTIVE
    usage_count: int = 0      # How often used (for auto-suggestion)
    created_at: str = ""
    
    # Review workflow fields
    created_by: str = "system"     # Who created (system or admin username)
    approved_by: str = ""          # Who approved (for PENDING -> ACTIVE)
    review_notes: str = ""         # Admin notes on approval/rejection
    deprecated_to: str = ""        # If deprecated, the new context_key
    
    def matches(self, context_raw: str) -> bool:
        """Check if raw context matches this entry"""
        if self.status == ContextStatus.DEPRECATED:
            return False  # Don't match deprecated entries
        
        raw_lower = context_raw.lower().strip()
        
        if raw_lower == self.context_key:
            return True
        
        for alias in self.aliases:
            if alias.lower() == raw_lower:
                return True
        
        return False


@dataclass
class ContextMapping:
    """
    Result of context resolution with 2-3 token validation.
    
    Rules:
    - Optimal: 2-3 tokens (e.g., sql_queries, etl_orchestration)
    - 1 token: allowed but flagged needs_context_refine=True
    - >3 tokens: first 3 tokens kept, rest moved to overflow_tags
    """
    context_raw: str               # Original LLM extraction
    context_key: Optional[str]     # Normalized key (None if not in registry)
    domain_key: str
    is_normalized: bool            # Whether mapping to registry exists
    suggested_keys: List[str]      # Similar contexts in registry
    
    # 2-3 token validation
    token_count: int = 0           # Number of tokens in context
    needs_context_refine: bool = False  # True if 1 token (too generic)
    overflow_tags: List[str] = None     # Extra tokens beyond 3 (move to SemanticTags)
    
    def get_effective_context(self) -> str:
        """Get the context to use in concept_code"""
        return self.context_key if self.context_key else self.context_raw
    
    def __post_init__(self):
        if self.overflow_tags is None:
            self.overflow_tags = []


# ==========================================
# DEFAULT CONTEXT REGISTRY PER DOMAIN
# Seed contexts (7 per domain) for initial alias mapping
# ==========================================

DEFAULT_REGISTRY: Dict[str, List[ContextEntry]] = {
    # ========================================
    # MIS - Management Information System
    # ========================================
    "mis": [
        ContextEntry("sql_basics", "SQL Basics", "mis", 
                    ["sql", "basic_sql", "sql_fundamentals", "sql_intro"]),
        ContextEntry("database_design", "Database Design", "mis",
                    ["db_design", "schema_design", "database_modeling", "er_diagram"]),
        ContextEntry("systems_analysis", "Systems Analysis", "mis",
                    ["analysis", "system_analysis", "business_analysis", "requirements"]),
        ContextEntry("business_process", "Business Process", "mis",
                    ["process", "workflow", "bpm", "process_modeling"]),
        ContextEntry("requirements_modeling", "Requirements Modeling", "mis",
                    ["requirements", "use_case", "user_stories", "specification"]),
        ContextEntry("erp_overview", "ERP Overview", "mis",
                    ["erp", "enterprise_systems", "sap", "oracle"]),
        ContextEntry("data_governance", "Data Governance", "mis",
                    ["governance", "data_quality", "data_management", "metadata"]),
    ],
    
    # ========================================
    # BI - Business Intelligence
    # ========================================
    "bi": [
        ContextEntry("kpi_design", "KPI Design", "bi",
                    ["kpi", "metrics", "indicators", "performance_metrics"]),
        ContextEntry("dashboarding", "Dashboarding", "bi",
                    ["dashboard", "dashboards", "dashboard_design", "ui_analytics"]),
        ContextEntry("dimensional_modeling", "Dimensional Modeling", "bi",
                    ["star_schema", "snowflake", "olap", "cube"]),
        ContextEntry("reporting", "Reporting", "bi",
                    ["reports", "report_design", "business_reports", "ad_hoc"]),
        ContextEntry("data_visualization", "Data Visualization", "bi",
                    ["visualization", "charts", "graphs", "visual_analytics"]),
        ContextEntry("bi_tools", "BI Tools", "bi",
                    ["tableau", "power_bi", "looker", "qlik"]),
        ContextEntry("metrics_storytelling", "Metrics Storytelling", "bi",
                    ["storytelling", "data_story", "narrative", "insights"]),
    ],
    
    # ========================================
    # DE - Data Engineering
    # ========================================
    "de": [
        ContextEntry("etl_orchestration", "ETL Orchestration", "de",
                    ["etl", "elt", "data_pipeline", "orchestration"]),
        ContextEntry("data_modeling", "Data Modeling", "de",
                    ["modeling", "schema", "data_models", "entities"]),
        ContextEntry("data_quality", "Data Quality", "de",
                    ["quality", "validation", "testing", "dq"]),
        ContextEntry("stream_processing", "Stream Processing", "de",
                    ["streaming", "kafka", "real_time", "event_driven"]),
        ContextEntry("batch_processing", "Batch Processing", "de",
                    ["batch", "spark", "hadoop", "distributed"]),
        ContextEntry("data_lakehouse", "Data Lakehouse", "de",
                    ["lakehouse", "data_lake", "delta_lake", "iceberg"]),
        ContextEntry("pipeline_monitoring", "Pipeline Monitoring", "de",
                    ["monitoring", "observability", "alerting", "logging"]),
    ],
    
    # ========================================
    # DS - Data Science
    # ========================================
    "ds": [
        ContextEntry("statistics_foundation", "Statistics Foundation", "ds",
                    ["statistics", "stats", "probability", "distributions"]),
        ContextEntry("feature_engineering", "Feature Engineering", "ds",
                    ["features", "feature_selection", "encoding", "scaling"]),
        ContextEntry("model_training", "Model Training", "ds",
                    ["training", "fitting", "optimization", "learning"]),
        ContextEntry("model_evaluation", "Model Evaluation", "ds",
                    ["evaluation", "metrics", "validation", "testing"]),
        ContextEntry("experimentation", "Experimentation", "ds",
                    ["experiments", "ab_testing", "hypothesis", "trials"]),
        ContextEntry("data_preprocessing", "Data Preprocessing", "ds",
                    ["preprocessing", "cleaning", "wrangling", "transformation"]),
        ContextEntry("ml_basics", "ML Basics", "ds",
                    ["ml", "machine_learning", "algorithms", "supervised"]),
    ],
    
    # ========================================
    # AIE - AI Engineering
    # ========================================
    "aie": [
        ContextEntry("mlops_deployment", "MLOps Deployment", "aie",
                    ["mlops", "deployment", "ci_cd", "automation"]),
        ContextEntry("model_serving", "Model Serving", "aie",
                    ["serving", "inference", "api", "endpoints"]),
        ContextEntry("llm_rag", "LLM RAG", "aie",
                    ["rag", "retrieval", "augmented_generation", "vector_search"]),
        ContextEntry("prompt_engineering", "Prompt Engineering", "aie",
                    ["prompts", "prompt_design", "few_shot", "chain_of_thought"]),
        ContextEntry("evaluation_observability", "Evaluation & Observability", "aie",
                    ["observability", "tracing", "evaluation", "benchmarks"]),
        ContextEntry("safety_alignment", "Safety & Alignment", "aie",
                    ["safety", "alignment", "guardrails", "responsible_ai"]),
        ContextEntry("scalable_inference", "Scalable Inference", "aie",
                    ["scaling", "gpu", "optimization", "batching"]),
    ]
}


class ContextRegistry:
    """
    Registry for context normalization.
    
    Lifecycle:
    1. LLM extracts context_raw from document
    2. Registry attempts to map to context_key
    3. If no match, context_raw is used (nullable context_key)
    4. Admin can add new entries / aliases over time
    """
    
    # Validation rules for context_raw
    CONTEXT_PATTERN = re.compile(r'^[a-z][a-z0-9_]{1,50}$')
    
    def __init__(self, domain_key: str = None):
        """Initialize with optional domain filter"""
        self.domain_key = domain_key
        self._registry: Dict[str, List[ContextEntry]] = {}
        self._load_defaults()
        
        # Track raw contexts that couldn't be normalized (legacy)
        self._unmapped_contexts: Dict[str, int] = {}
        
        # Admin review workflow tracking
        self._pending_contexts: Dict[str, PendingContext] = {}  # key = "domain:context_raw"
        self._rejected_contexts: Dict[str, Dict] = {}  # Rejected with review notes
    
    def _load_defaults(self):
        """Load default registry entries"""
        self._registry = {
            domain: list(entries) 
            for domain, entries in DEFAULT_REGISTRY.items()
        }
    
    def resolve(self, context_raw: str, domain_key: str) -> ContextMapping:
        """
        Resolve raw context to normalized key.
        
        Args:
            context_raw: LLM-extracted context
            domain_key: Domain this context belongs to
            
        Returns:
            ContextMapping with context_key (or None if not in registry)
        """
        # Normalize to 2-3 tokens
        normalized, token_count, overflow_tags = self._normalize_context(context_raw)
        needs_refine = token_count == 1
        
        # Get domain entries
        entries = self._registry.get(domain_key, [])
        
        # Try exact match first
        for entry in entries:
            if entry.matches(normalized):
                entry.usage_count += 1
                return ContextMapping(
                    context_raw=normalized,
                    context_key=entry.context_key,
                    domain_key=domain_key,
                    is_normalized=True,
                    suggested_keys=[],
                    token_count=token_count,
                    needs_context_refine=needs_refine,
                    overflow_tags=overflow_tags
                )
        
        # No match - find similar contexts for suggestions
        suggestions = self._find_similar(normalized, entries)
        
        # Track unmapped context for admin review
        self._unmapped_contexts[normalized] = self._unmapped_contexts.get(normalized, 0) + 1
        
        return ContextMapping(
            context_raw=normalized,
            context_key=None,  # Not in registry yet
            domain_key=domain_key,
            is_normalized=False,
            suggested_keys=suggestions[:3],
            token_count=token_count,
            needs_context_refine=needs_refine,
            overflow_tags=overflow_tags
        )
    
    def _normalize_context(self, context: str) -> tuple:
        """
        Normalize context to 2-3 tokens snake_case format.
        
        Rules:
        - Optimal: 2-3 tokens (sql_queries, etl_orchestration)
        - 1 token: allowed but flagged (too generic)
        - >3 tokens: keep first 3, move rest to overflow_tags
        - Max 32 chars, [a-z0-9_] only
        
        Returns:
            (normalized_context, token_count, overflow_tags)
        """
        if not context:
            return "general", 1, []
        
        # Step 1: Basic cleanup
        result = context.lower()
        result = result.replace("-", "_").replace(" ", "_")
        result = re.sub(r'[^a-z0-9_]', '', result)
        result = re.sub(r'_+', '_', result)
        result = result.strip("_")
        
        if not result:
            return "general", 1, []
        
        # Step 2: Split into tokens
        tokens = [t for t in result.split("_") if t]
        token_count = len(tokens)
        
        # Step 3: Apply 2-3 token rule
        overflow_tags = []
        if token_count > 3:
            # Keep first 3 tokens, move rest to overflow
            overflow_tags = tokens[3:]
            tokens = tokens[:3]
        
        # Step 4: Rebuild normalized context
        normalized = "_".join(tokens)
        
        # Step 5: Enforce max length (32 chars)
        if len(normalized) > 32:
            # Truncate but keep meaningful suffix
            normalized = normalized[:32].rstrip("_")
        
        return normalized, len(tokens), overflow_tags
    
    def _sanitize(self, context: str) -> str:
        """Legacy sanitize (wraps normalize_context)"""
        normalized, _, _ = self._normalize_context(context)
        return normalized

    
    def _find_similar(self, context_raw: str, entries: List[ContextEntry]) -> List[str]:
        """Find similar contexts in registry (for suggestions)"""
        similar = []
        
        for entry in entries:
            # Check prefix match
            if entry.context_key.startswith(context_raw[:3]):
                similar.append(entry.context_key)
            # Check word overlap
            elif any(word in entry.context_key for word in context_raw.split("_")):
                similar.append(entry.context_key)
        
        return similar
    
    def add_entry(
        self, 
        domain_key: str,
        context_key: str,
        display_name: str,
        aliases: List[str] = None
    ) -> bool:
        """Add new context to registry (admin operation)"""
        if domain_key not in self._registry:
            self._registry[domain_key] = []
        
        # Check for duplicates
        for entry in self._registry[domain_key]:
            if entry.context_key == context_key:
                # Update aliases
                entry.aliases.extend(aliases or [])
                return True
        
        # Add new entry
        self._registry[domain_key].append(ContextEntry(
            context_key=context_key,
            display_name=display_name,
            domain_key=domain_key,
            aliases=aliases or [],
            created_at=datetime.now().isoformat()
        ))
        
        return True
    
    def add_alias(self, domain_key: str, context_key: str, alias: str) -> bool:
        """Add alias to existing context (for gradual normalization)"""
        entries = self._registry.get(domain_key, [])
        
        for entry in entries:
            if entry.context_key == context_key:
                if alias not in entry.aliases:
                    entry.aliases.append(alias)
                return True
        
        return False
    
    def get_unmapped_contexts(self, min_count: int = 2) -> Dict[str, int]:
        """Get contexts that need admin review (frequently used but not mapped)"""
        return {
            ctx: count 
            for ctx, count in self._unmapped_contexts.items() 
            if count >= min_count
        }
    
    def get_top_contexts(self, domain_key: str, limit: int = 10) -> List[str]:
        """Get most used contexts for a domain (for UI suggestions)"""
        entries = self._registry.get(domain_key, [])
        entries.sort(key=lambda e: e.usage_count, reverse=True)
        return [e.context_key for e in entries[:limit]]
    
    def list_contexts(self, domain_key: str = None) -> List[Dict[str, Any]]:
        """List all contexts, optionally filtered by domain"""
        result = []
        
        domains = [domain_key] if domain_key else self._registry.keys()
        
        for domain in domains:
            for entry in self._registry.get(domain, []):
                result.append({
                    "context_key": entry.context_key,
                    "display_name": entry.display_name,
                    "domain_key": entry.domain_key,
                    "aliases": entry.aliases,
                    "usage_count": entry.usage_count
                })
        
        return result
    
    def is_valid_context(self, context: str) -> bool:
        """Check if context follows format rules"""
        return bool(self.CONTEXT_PATTERN.match(context))
    
    # ==========================================
    # ADMIN REVIEW WORKFLOW
    # ==========================================
    
    def get_pending_for_review(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get pending contexts that meet review triggers.
        
        Triggers (per proposal):
        - freq >= 5 in 7 days
        - freq >= 2 with >= 2 documents
        
        Returns top contexts by frequency for batch review.
        """
        pending = []
        for key, ctx in self._pending_contexts.items():
            if ctx.needs_review():
                pending.append(ctx.to_dict())
        
        # Sort by frequency descending
        pending.sort(key=lambda x: x["frequency"], reverse=True)
        return pending[:limit]
    
    def approve_context(
        self,
        context_raw: str,
        domain_key: str,
        context_key: str = None,
        display_name: str = None,
        admin_user: str = "admin",
        review_notes: str = ""
    ) -> bool:
        """
        Approve a pending context and promote to registry.
        
        Args:
            context_raw: The raw context being approved
            domain_key: Domain
            context_key: Canonical key (defaults to context_raw)
            display_name: Human-readable name
            admin_user: Who approved
            review_notes: Optional notes
            
        Returns:
            True if approved successfully
        """
        context_key = context_key or context_raw
        display_name = display_name or context_key.replace("_", " ").title()
        
        # Check if context_key already exists
        existing = self._find_entry(domain_key, context_key)
        
        if existing:
            # Add as alias to existing entry
            if context_raw not in existing.aliases:
                existing.aliases.append(context_raw)
            existing.review_notes = review_notes
            existing.approved_by = admin_user
        else:
            # Create new entry
            if domain_key not in self._registry:
                self._registry[domain_key] = []
            
            new_entry = ContextEntry(
                context_key=context_key,
                display_name=display_name,
                domain_key=domain_key,
                aliases=[context_raw] if context_raw != context_key else [],
                status=ContextStatus.ACTIVE,
                created_at=datetime.now().isoformat(),
                created_by="admin",
                approved_by=admin_user,
                review_notes=review_notes
            )
            self._registry[domain_key].append(new_entry)
        
        # Remove from pending
        pending_key = f"{domain_key}:{context_raw}"
        if pending_key in self._pending_contexts:
            del self._pending_contexts[pending_key]
        
        return True
    
    def reject_context(
        self,
        context_raw: str,
        domain_key: str,
        admin_user: str = "admin",
        review_notes: str = "",
        suggested_alternative: str = None
    ) -> bool:
        """
        Reject a pending context (keep in nodes but don't promote).
        
        Args:
            context_raw: The raw context being rejected
            domain_key: Domain
            admin_user: Who rejected
            review_notes: Why rejected (e.g., "too generic")
            suggested_alternative: Suggest a better context_key
        """
        pending_key = f"{domain_key}:{context_raw}"
        
        if pending_key in self._pending_contexts:
            # Store rejection info (context stays in nodes as context_raw)
            self._rejected_contexts[pending_key] = {
                "context_raw": context_raw,
                "domain_key": domain_key,
                "rejected_by": admin_user,
                "rejected_at": datetime.now().isoformat(),
                "review_notes": review_notes,
                "suggested_alternative": suggested_alternative
            }
            del self._pending_contexts[pending_key]
        
        return True
    
    def deprecate_context(
        self,
        domain_key: str,
        old_context_key: str,
        new_context_key: str,
        admin_user: str = "admin",
        review_notes: str = ""
    ) -> bool:
        """
        Deprecate a context_key and map to a new one.
        
        Use when merging/renaming contexts (e.g., dashboarding -> data_visualization).
        """
        old_entry = self._find_entry(domain_key, old_context_key)
        new_entry = self._find_entry(domain_key, new_context_key)
        
        if not old_entry:
            return False
        
        # Mark old as deprecated
        old_entry.status = ContextStatus.DEPRECATED
        old_entry.deprecated_to = new_context_key
        old_entry.review_notes = review_notes
        
        # Add old key as alias to new entry
        if new_entry:
            if old_context_key not in new_entry.aliases:
                new_entry.aliases.append(old_context_key)
            # Also migrate aliases
            for alias in old_entry.aliases:
                if alias not in new_entry.aliases:
                    new_entry.aliases.append(alias)
        
        return True
    
    def _find_entry(self, domain_key: str, context_key: str) -> Optional[ContextEntry]:
        """Find entry by context_key"""
        for entry in self._registry.get(domain_key, []):
            if entry.context_key == context_key:
                return entry
        return None
    
    def record_context_usage(
        self,
        context_raw: str,
        domain_key: str,
        document_id: str = None
    ):
        """Record usage of unmapped context for pending tracking"""
        pending_key = f"{domain_key}:{context_raw}"
        
        if pending_key not in self._pending_contexts:
            self._pending_contexts[pending_key] = PendingContext(
                context_raw=context_raw,
                domain_key=domain_key
            )
        
        self._pending_contexts[pending_key].record_usage(document_id)


# ==========================================
# SINGLETON INSTANCE
# ==========================================

_context_registry: Optional[ContextRegistry] = None


def get_context_registry() -> ContextRegistry:
    """Get singleton ContextRegistry instance"""
    global _context_registry
    if _context_registry is None:
        _context_registry = ContextRegistry()
    return _context_registry
