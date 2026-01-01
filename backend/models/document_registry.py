# Document Registry Model for Idempotent Ingestion
"""
Document Registry: Track document ingestion status for idempotency.
Ensures "file added twice" doesn't create duplicate concepts.
"""

import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import json


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "PENDING"           # Queued for processing
    PROCESSING = "PROCESSING"     # Currently extracting
    VALIDATED = "VALIDATED"       # Extraction complete, validation passed
    COMMITTED = "COMMITTED"       # Promoted to Course KG
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS" # Some chunks failed, others committed
    FAILED = "FAILED"             # Processing failed
    SKIPPED = "SKIPPED"           # Duplicate checksum, skipped


class ExtractionVersion(str, Enum):
    """Extraction pipeline version for reproducibility"""
    V1_BASIC = "v1_basic"                     # Original 3-layer extraction
    V2_PRODUCTION = "v2_production"           # With staging + validation
    V3_ENTITY_RESOLUTION = "v3_entity_res"    # With embedding-based merge


@dataclass
class DocumentRecord:
    """
    Document Registry Record.
    
    Tracks:
    - File identity (checksum)
    - Processing status
    - Extraction metadata for reproducibility
    - Audit trail
    """
    document_id: str
    filename: str
    checksum: str                              # SHA256 of file content
    status: DocumentStatus = DocumentStatus.PENDING
    
    # Extraction metadata
    extraction_version: ExtractionVersion = ExtractionVersion.V3_ENTITY_RESOLUTION
    model_name: str = "gemini-1.5-flash"
    chunk_count: int = 0
    concept_count: int = 0
    relationship_count: int = 0
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # Provenance
    extracted_concept_ids: list = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "checksum": self.checksum,
            "status": self.status.value,
            "extraction_version": self.extraction_version.value,
            "model_name": self.model_name,
            "chunk_count": self.chunk_count,
            "concept_count": self.concept_count,
            "relationship_count": self.relationship_count,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "extracted_concept_ids": self.extracted_concept_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentRecord":
        """Create from dictionary"""
        return cls(
            document_id=data["document_id"],
            filename=data["filename"],
            checksum=data["checksum"],
            status=DocumentStatus(data["status"]),
            extraction_version=ExtractionVersion(data.get("extraction_version", "v3_entity_res")),
            model_name=data.get("model_name", "gemini-1.5-flash"),
            chunk_count=data.get("chunk_count", 0),
            concept_count=data.get("concept_count", 0),
            relationship_count=data.get("relationship_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            extracted_concept_ids=data.get("extracted_concept_ids", [])
        )


class DocumentRegistry:
    """
    Document Registry for idempotent ingestion.
    
    Features:
    - Checksum-based deduplication
    - Status tracking
    - Audit trail
    """
    
    def __init__(self, state_manager=None):
        self.state_manager = state_manager
        self._cache: Dict[str, DocumentRecord] = {}
    
    @staticmethod
    def compute_checksum(content: str) -> str:
        """Compute SHA256 checksum of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def check_exists(self, checksum: str) -> Optional[DocumentRecord]:
        """Check if document with this checksum already processed"""
        # Check cache first
        for record in self._cache.values():
            if record.checksum == checksum:
                return record
        
        # Check persistent storage (Redis or PostgreSQL)
        if self.state_manager:
            stored = await self.state_manager.redis.get(f"doc_registry:{checksum}")
            if stored:
                record = DocumentRecord.from_dict(json.loads(stored))
                self._cache[record.document_id] = record
                return record
        
        return None
    
    async def register(self, document_id: str, filename: str, content: str, force_override: bool = False) -> DocumentRecord:
        """Register new document for processing"""
        checksum = self.compute_checksum(content)
        
        # Check for existing
        if not force_override:
            existing = await self.check_exists(checksum)
            if existing and existing.status in [DocumentStatus.COMMITTED, DocumentStatus.VALIDATED]:
                existing.status = DocumentStatus.SKIPPED
                return existing
        
        # Create new record
        record = DocumentRecord(
            document_id=document_id,
            filename=filename,
            checksum=checksum,
            status=DocumentStatus.PENDING
        )
        
        self._cache[document_id] = record
        
        # Persist
        if self.state_manager:
            await self.state_manager.redis.set(
                f"doc_registry:{checksum}",
                json.dumps(record.to_dict()),
                ttl=86400 * 30  # 30 days
            )
        
        return record
    
    async def update_status(
        self, 
        document_id: str, 
        status: DocumentStatus,
        **kwargs
    ) -> Optional[DocumentRecord]:
        """Update document status"""
        record = self._cache.get(document_id)
        if not record:
            return None
        
        record.status = status
        
        # Update timing
        if status == DocumentStatus.PROCESSING:
            record.started_at = datetime.now()
        elif status in [DocumentStatus.COMMITTED, DocumentStatus.FAILED]:
            record.completed_at = datetime.now()
        
        # Update other fields
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        # Persist
        if self.state_manager:
            await self.state_manager.redis.set(
                f"doc_registry:{record.checksum}",
                json.dumps(record.to_dict()),
                ttl=86400 * 30
            )
        
        return record
    
    async def get_record(self, document_id: str) -> Optional[DocumentRecord]:
        """Get document record by ID"""
        return self._cache.get(document_id)
    
    async def get_all_records(self) -> list:
        """Get all document records"""
        return list(self._cache.values())
