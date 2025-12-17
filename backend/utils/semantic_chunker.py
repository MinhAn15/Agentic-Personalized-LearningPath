# Semantic Chunker for Knowledge Extraction
"""
Semantic Chunker: Split documents by headings/sections instead of arbitrary character limits.

Benefits:
- Preserves relationships within sections
- Reproducible chunking
- Better context for LLM extraction
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ChunkType(str, Enum):
    """Type of chunk based on source structure"""
    HEADING_1 = "HEADING_1"       # # Title
    HEADING_2 = "HEADING_2"       # ## Section
    HEADING_3 = "HEADING_3"       # ### Subsection
    PARAGRAPH = "PARAGRAPH"       # No heading, paragraph break
    CODE_BLOCK = "CODE_BLOCK"     # ```code```
    LIST_BLOCK = "LIST_BLOCK"     # Bulleted/numbered list
    RAW = "RAW"                   # Fallback raw split


@dataclass
class SemanticChunk:
    """
    A semantic chunk from a document.
    
    Contains:
    - Content text
    - Metadata for provenance
    - Hierarchy information
    """
    chunk_id: str
    content: str
    chunk_type: ChunkType
    
    # Position in document
    chunk_index: int
    start_char: int
    end_char: int
    
    # Hierarchy
    source_heading: str              # Parent heading
    heading_path: List[str]          # Full path: ["Chapter 1", "Section 1.1", "1.1.1"]
    
    # Metadata
    word_count: int
    has_code: bool
    has_list: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "chunk_type": self.chunk_type.value,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "source_heading": self.source_heading,
            "heading_path": self.heading_path,
            "word_count": self.word_count,
            "has_code": self.has_code,
            "has_list": self.has_list
        }


class SemanticChunker:
    """
    Semantic Chunker: Split by headings/sections.
    
    Strategy:
    1. Try to split by ## headings (Heading 2)
    2. If chunk too large, split by ### headings (Heading 3)
    3. If still too large, split by paragraphs
    4. Fallback: split by max_chunk_size with overlap
    
    Preserves:
    - Heading hierarchy
    - Code blocks (don't split mid-block)
    - List blocks (don't split mid-list)
    """
    
    # Regex patterns
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r'```[\s\S]*?```', re.MULTILINE)
    LIST_PATTERN = re.compile(r'^[\s]*[-*+]\s+.+$', re.MULTILINE)
    NUMBERED_LIST_PATTERN = re.compile(r'^[\s]*\d+\.\s+.+$', re.MULTILINE)
    
    def __init__(
        self,
        max_chunk_size: int = 4000,      # Target max characters per chunk
        min_chunk_size: int = 500,        # Minimum chunk size (avoid tiny chunks)
        overlap_size: int = 200,          # Overlap for fallback splitting
        preserve_code_blocks: bool = True
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_size = overlap_size
        self.preserve_code_blocks = preserve_code_blocks
    
    def chunk(self, document: str, document_id: str = "doc") -> List[SemanticChunk]:
        """
        Main chunking method.
        
        Args:
            document: Full document text
            document_id: ID for chunk naming
            
        Returns:
            List of SemanticChunk objects
        """
        if not document or not document.strip():
            return []
        
        # Step 1: Protect code blocks (replace with placeholders)
        document_protected, code_blocks = self._protect_code_blocks(document)
        
        # Step 2: Split by headings
        sections = self._split_by_headings(document_protected)
        
        # Step 3: Process each section
        chunks = []
        chunk_index = 0
        
        for section in sections:
            # Restore code blocks in this section
            section_content = self._restore_code_blocks(section["content"], code_blocks)
            
            # Check if section needs further splitting
            if len(section_content) > self.max_chunk_size:
                # Split large section by paragraphs
                sub_chunks = self._split_by_paragraphs(
                    section_content, 
                    section["heading"],
                    section["heading_path"]
                )
            else:
                sub_chunks = [(section_content, section["heading"], section["heading_path"])]
            
            # Create SemanticChunk objects
            for content, heading, path in sub_chunks:
                if len(content.strip()) < self.min_chunk_size and len(chunks) > 0:
                    # Merge tiny chunk with previous
                    chunks[-1] = SemanticChunk(
                        chunk_id=chunks[-1].chunk_id,
                        content=chunks[-1].content + "\n\n" + content,
                        chunk_type=chunks[-1].chunk_type,
                        chunk_index=chunks[-1].chunk_index,
                        start_char=chunks[-1].start_char,
                        end_char=chunks[-1].end_char + len(content) + 2,
                        source_heading=chunks[-1].source_heading,
                        heading_path=chunks[-1].heading_path,
                        word_count=len(chunks[-1].content.split()) + len(content.split()),
                        has_code=chunks[-1].has_code or "```" in content,
                        has_list=chunks[-1].has_list or bool(self.LIST_PATTERN.search(content))
                    )
                    continue
                
                chunk = SemanticChunk(
                    chunk_id=f"{document_id}_chunk_{chunk_index}",
                    content=content.strip(),
                    chunk_type=self._determine_chunk_type(content, heading),
                    chunk_index=chunk_index,
                    start_char=section.get("start", 0),
                    end_char=section.get("end", len(content)),
                    source_heading=heading,
                    heading_path=path,
                    word_count=len(content.split()),
                    has_code="```" in content,
                    has_list=bool(self.LIST_PATTERN.search(content))
                )
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks
    
    def _protect_code_blocks(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Replace code blocks with placeholders to prevent splitting"""
        code_blocks = {}
        
        def replacer(match):
            placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
            code_blocks[placeholder] = match.group(0)
            return placeholder
        
        protected = self.CODE_BLOCK_PATTERN.sub(replacer, text)
        return protected, code_blocks
    
    def _restore_code_blocks(self, text: str, code_blocks: Dict[str, str]) -> str:
        """Restore code blocks from placeholders"""
        for placeholder, code in code_blocks.items():
            text = text.replace(placeholder, code)
        return text
    
    def _split_by_headings(self, document: str) -> List[Dict[str, Any]]:
        """Split document by headings, tracking hierarchy"""
        sections = []
        current_path = []
        
        # Find all headings
        headings = list(self.HEADING_PATTERN.finditer(document))
        
        if not headings:
            # No headings - treat entire document as one section
            return [{
                "content": document,
                "heading": "Document",
                "heading_path": ["Document"],
                "level": 0,
                "start": 0,
                "end": len(document)
            }]
        
        # Process each section between headings
        for i, match in enumerate(headings):
            level = len(match.group(1))  # Number of #
            heading_text = match.group(2).strip()
            
            # Update heading path
            while len(current_path) >= level:
                current_path.pop()
            current_path.append(heading_text)
            
            # Get content (from this heading to next, or end)
            start = match.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(document)
            content = document[start:end].strip()
            
            if content:  # Only add non-empty sections
                sections.append({
                    "content": f"{'#' * level} {heading_text}\n\n{content}",
                    "heading": heading_text,
                    "heading_path": current_path.copy(),
                    "level": level,
                    "start": match.start(),
                    "end": end
                })
        
        # Add content before first heading if exists
        first_heading_start = headings[0].start()
        if first_heading_start > 0:
            preamble = document[:first_heading_start].strip()
            if preamble:
                sections.insert(0, {
                    "content": preamble,
                    "heading": "Introduction",
                    "heading_path": ["Introduction"],
                    "level": 0,
                    "start": 0,
                    "end": first_heading_start
                })
        
        return sections
    
    def _split_by_paragraphs(
        self, 
        content: str, 
        heading: str,
        heading_path: List[str]
    ) -> List[Tuple[str, str, List[str]]]:
        """Split large section by paragraphs"""
        paragraphs = re.split(r'\n\n+', content)
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > self.max_chunk_size:
                if current_chunk:
                    chunks.append((current_chunk, heading, heading_path))
                current_chunk = para
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para
        
        if current_chunk:
            chunks.append((current_chunk, heading, heading_path))
        
        # If still too large, do raw split with overlap
        final_chunks = []
        for chunk_content, h, hp in chunks:
            if len(chunk_content) > self.max_chunk_size * 1.5:
                # Raw split as last resort
                raw_chunks = self._raw_split(chunk_content)
                for rc in raw_chunks:
                    final_chunks.append((rc, h, hp))
            else:
                final_chunks.append((chunk_content, h, hp))
        
        return final_chunks
    
    def _raw_split(self, text: str) -> List[str]:
        """Fallback: split by character limit with overlap"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.max_chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end within overlap zone
                for punct in ['. ', '? ', '! ', '\n']:
                    last_punct = text.rfind(punct, start + self.max_chunk_size - self.overlap_size, end)
                    if last_punct != -1:
                        end = last_punct + 1
                        break
            
            chunks.append(text[start:end])
            start = end - self.overlap_size if end < len(text) else end
        
        return chunks
    
    def _determine_chunk_type(self, content: str, heading: str) -> ChunkType:
        """Determine the type of chunk"""
        if heading.startswith("# ") or heading.startswith("# "):
            return ChunkType.HEADING_1
        elif "## " in content[:50]:
            return ChunkType.HEADING_2
        elif "### " in content[:50]:
            return ChunkType.HEADING_3
        elif self.CODE_BLOCK_PATTERN.search(content):
            return ChunkType.CODE_BLOCK
        elif self.LIST_PATTERN.search(content) or self.NUMBERED_LIST_PATTERN.search(content):
            return ChunkType.LIST_BLOCK
        else:
            return ChunkType.PARAGRAPH
    
    def get_stats(self, chunks: List[SemanticChunk]) -> Dict[str, Any]:
        """Get statistics about chunking results"""
        if not chunks:
            return {"total_chunks": 0}
        
        word_counts = [c.word_count for c in chunks]
        char_counts = [len(c.content) for c in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_words": sum(word_counts),
            "total_chars": sum(char_counts),
            "avg_words_per_chunk": sum(word_counts) / len(chunks),
            "avg_chars_per_chunk": sum(char_counts) / len(chunks),
            "min_chars": min(char_counts),
            "max_chars": max(char_counts),
            "chunks_with_code": sum(1 for c in chunks if c.has_code),
            "chunks_with_lists": sum(1 for c in chunks if c.has_list),
            "chunk_types": {t.value: sum(1 for c in chunks if c.chunk_type == t) for t in ChunkType}
        }
