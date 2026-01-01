# Pure Agentic Semantic Chunker for Knowledge Extraction
"""
Pure Agentic Semantic Chunker: Uses LLM reasoning to split documents 
instead of regex/rule-based logic.

Philosophy:
- Maximize AI capabilities, minimize traditional code logic
- AI understands invisible boundaries (tone shifts, metaphor endings)
- Future-proof: Better models = better chunking without code changes

Pipeline:
1. Architect Phase: LLM creates logical Table of Contents from idea flows
2. Refiner Phase: LLM self-reviews using Reflexion technique
3. Executor Phase: Extract content based on refined plan
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ChunkType(str, Enum):
    """Type of chunk based on semantic analysis"""
    CONCEPT_INTRO = "CONCEPT_INTRO"      # Introduction of a new concept
    EXPLANATION = "EXPLANATION"           # Detailed explanation
    EXAMPLE = "EXAMPLE"                   # Examples and illustrations
    PRACTICE = "PRACTICE"                 # Exercises or practice problems
    SUMMARY = "SUMMARY"                   # Summary or conclusion
    TRANSITION = "TRANSITION"             # Transitional content
    MIXED = "MIXED"                       # Mixed content types


@dataclass
class SemanticChunk:
    """
    A semantic chunk from a document.
    
    Contains:
    - Content text
    - Metadata for provenance
    - AI-determined structure information
    """
    chunk_id: str
    content: str
    chunk_type: ChunkType
    
    # Position in document
    chunk_index: int
    start_char: int
    end_char: int
    
    # AI-determined hierarchy
    source_heading: str              # AI-inferred topic
    heading_path: List[str]          # Logical path in document structure
    
    # Metadata
    word_count: int
    pedagogical_purpose: str         # What this chunk teaches
    
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
            "pedagogical_purpose": self.pedagogical_purpose
        }


class AgenticChunker:
    """
    Pure Agentic Chunker: Uses LLM reasoning for document segmentation.
    
    Pipeline:
    1. Architect: LLM analyzes document and proposes logical boundaries
    2. Refiner: LLM self-reviews and fixes segmentation errors (Reflexion)
    3. Executor: Extract content based on refined plan
    
    No regex, no rule-based logic - pure AI reasoning.
    """
    
    def __init__(
        self,
        llm,
        max_chunk_size: int = 4000,
        min_chunk_size: int = 500
    ):
        """
        Initialize Agentic Chunker.
        
        Args:
            llm: LLM instance (e.g., Gemini) for reasoning
            max_chunk_size: Soft limit for chunk size (AI will respect this)
            min_chunk_size: Minimum chunk size (AI will merge small chunks)
        """
        self.llm = llm
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.logger = logging.getLogger(f"{__name__}.AgenticChunker")
    
    async def chunk_with_ai(
        self, 
        document: str, 
        document_id: str = "doc",
        document_title: str = "Untitled"
    ) -> List[SemanticChunk]:
        """
        Main async chunking method using 3-phase AI pipeline.
        
        Args:
            document: Full document text (any format - plain text, markdown, etc.)
            document_id: ID for chunk naming
            document_title: Title for context
            
        Returns:
            List of SemanticChunk objects
        """
        if not document or not document.strip():
            return []
        
        self.logger.info(f"🧠 [Agentic Chunker] Starting 3-phase pipeline for: {document_title}")
        
        # Phase 1: Architect - Create logical structure
        structure = await self._architect_phase(document, document_title)
        self.logger.info(f"📐 [Architect] Proposed {len(structure)} sections")
        
        # Phase 2: Refiner - Self-review with Reflexion
        refined_structure = await self._refiner_phase(document, structure)
        self.logger.info(f"🔍 [Refiner] Refined to {len(refined_structure)} sections")
        
        # Phase 3: Executor - Extract chunks based on refined plan
        chunks = await self._executor_phase(document, refined_structure, document_id)
        self.logger.info(f"✅ [Executor] Created {len(chunks)} semantic chunks")
        
        return chunks
    
    async def _architect_phase(
        self, 
        document: str, 
        document_title: str
    ) -> List[Dict[str, Any]]:
        """
        Phase 1: The Architect
        
        LLM analyzes the entire document and creates a logical 
        Table of Contents based on idea flows, regardless of formatting.
        """
        prompt = f"""You are an expert document analyst. Analyze this educational document and identify logical sections based on the FLOW OF IDEAS, not formatting.

Document Title: {document_title}
Document Content:
---
{document}
---

Your task:
1. Read the entire document carefully
2. Identify where topics/concepts BEGIN and END based on semantic meaning
3. Create a logical Table of Contents that groups related content together

Rules:
- Each section should represent ONE complete pedagogical unit (concept + explanation + examples)
- Do NOT split examples from their concepts
- Do NOT split definitions from their explanations
- Aim for sections between {self.min_chunk_size} and {self.max_chunk_size} characters
- Ignore any existing formatting (headings, bullets) - focus on MEANING

Return a JSON array where each item has:
- "title": A descriptive title for this section
- "start_text": The EXACT first 50 characters of where this section begins
- "end_text": The EXACT last 50 characters of where this section ends
- "purpose": What this section teaches (1 sentence)
- "chunk_type": One of [CONCEPT_INTRO, EXPLANATION, EXAMPLE, PRACTICE, SUMMARY, TRANSITION, MIXED]

Example output:
[
  {{
    "title": "Introduction to Variables",
    "start_text": "Variables are fundamental building blocks",
    "end_text": "before moving to data types.",
    "purpose": "Introduces the concept of variables and their role in programming",
    "chunk_type": "CONCEPT_INTRO"
  }}
]

Return ONLY valid JSON array. No explanations before or after."""

        try:
            response = await self.llm.acomplete(prompt)
            structure = self._parse_json_array(response.text)
            return structure if structure else []
        except Exception as e:
            self.logger.error(f"Architect phase error: {e}")
            # Fallback: treat entire document as one chunk
            return [{
                "title": document_title,
                "start_text": document[:50] if len(document) > 50 else document,
                "end_text": document[-50:] if len(document) > 50 else document,
                "purpose": "Full document content",
                "chunk_type": "MIXED"
            }]
    
    async def _refiner_phase(
        self, 
        document: str, 
        structure: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Phase 2: The Refiner (Reflexion)
        
        LLM self-reviews its proposed boundaries and fixes segmentation errors.
        Uses Reflexion technique: AI critiques and improves its own output.
        """
        if not structure:
            return structure
        
        structure_json = self._to_json_string(structure)
        
        prompt = f"""You are reviewing a document segmentation plan. Your job is to find and fix errors.

Original Document (for reference):
---
{document[:2000]}...
---

Proposed Segmentation:
{structure_json}

CRITICAL REVIEW QUESTIONS:
1. Are any EXAMPLES being separated from their parent CONCEPTS? (BAD - merge them)
2. Are any sections too small (< {self.min_chunk_size} chars)? (BAD - merge with neighbors)
3. Are any sections too large (> {self.max_chunk_size} chars)? (Consider splitting if there's a natural break)
4. Does each section represent a COMPLETE learning unit? (A student should understand the topic without needing adjacent chunks)

If you find issues:
- Merge sections that should be together
- Split sections only at natural pedagogical boundaries
- Adjust titles and purposes as needed

Return the CORRECTED JSON array in the same format.
If no changes needed, return the original array.

Return ONLY valid JSON array. No explanations."""

        try:
            response = await self.llm.acomplete(prompt)
            refined = self._parse_json_array(response.text)
            return refined if refined else structure
        except Exception as e:
            self.logger.error(f"Refiner phase error: {e}")
            return structure
    
    async def _executor_phase(
        self, 
        document: str, 
        structure: List[Dict[str, Any]],
        document_id: str
    ) -> List[SemanticChunk]:
        """
        Phase 3: The Executor
        
        Extract actual content based on the refined structure.
        Uses fuzzy text matching to find section boundaries.
        """
        chunks = []
        
        for idx, section in enumerate(structure):
            start_text = section.get("start_text", "")
            end_text = section.get("end_text", "")
            
            # Find boundaries using fuzzy matching
            start_pos = self._fuzzy_find(document, start_text, search_start=0)
            end_pos = self._fuzzy_find(document, end_text, search_start=start_pos)
            
            if start_pos == -1:
                start_pos = 0
            if end_pos == -1 or end_pos <= start_pos:
                # If end not found, try to find next section's start
                if idx + 1 < len(structure):
                    next_start = structure[idx + 1].get("start_text", "")
                    next_pos = self._fuzzy_find(document, next_start, search_start=start_pos + 1)
                    end_pos = next_pos - 1 if next_pos > start_pos else len(document)
                else:
                    end_pos = len(document)
            else:
                end_pos = end_pos + len(end_text)
            
            content = document[start_pos:end_pos].strip()
            
            if content:
                chunk_type_str = section.get("chunk_type", "MIXED")
                try:
                    chunk_type = ChunkType(chunk_type_str)
                except ValueError:
                    chunk_type = ChunkType.MIXED
                
                chunk = SemanticChunk(
                    chunk_id=f"{document_id}_chunk_{idx}",
                    content=content,
                    chunk_type=chunk_type,
                    chunk_index=idx,
                    start_char=start_pos,
                    end_char=end_pos,
                    source_heading=section.get("title", f"Section {idx + 1}"),
                    heading_path=[section.get("title", f"Section {idx + 1}")],
                    word_count=len(content.split()),
                    pedagogical_purpose=section.get("purpose", "")
                )
                chunks.append(chunk)
        
        return chunks
    
    def _fuzzy_find(self, text: str, pattern: str, search_start: int = 0) -> int:
        """
        Find pattern in text with some tolerance for whitespace differences.
        """
        if not pattern:
            return -1
        
        # Normalize whitespace
        normalized_pattern = ' '.join(pattern.split())
        normalized_text = ' '.join(text[search_start:].split())
        
        # Try exact match first
        pos = text.find(pattern, search_start)
        if pos != -1:
            return pos
        
        # Try normalized match
        normalized_pos = normalized_text.find(normalized_pattern)
        if normalized_pos != -1:
            # Convert back to original position (approximate)
            return search_start + normalized_pos
        
        # Try first few words
        words = normalized_pattern.split()[:5]
        if words:
            partial = ' '.join(words)
            pos = text.lower().find(partial.lower(), search_start)
            if pos != -1:
                return pos
        
        return -1
    
    def _parse_json_array(self, text: str) -> List[Dict]:
        """Parse JSON array from LLM response."""
        
        # Clean up common LLM response issues
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            return []
        except json.JSONDecodeError:
            # Try to find JSON array in text
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return []
    
    def _to_json_string(self, obj: Any) -> str:
        """Convert object to JSON string."""
        return json.dumps(obj, indent=2, ensure_ascii=False)
    
    def get_stats(self, chunks: List[SemanticChunk]) -> Dict[str, Any]:
        """Get statistics about chunking results."""
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
            "chunk_types": {t.value: sum(1 for c in chunks if c.chunk_type == t) for t in ChunkType}
        }


# Backward compatibility: Keep old class name as alias
class SemanticChunker(AgenticChunker):
    """
    Backward compatibility alias for AgenticChunker.
    
    Note: For new code, use AgenticChunker directly.
    This class requires an LLM instance for the AI pipeline.
    
    Deprecated Parameters (kept for backward compatibility):
    - overlap_size: Ignored in agentic approach
    - preserve_code_blocks: Handled by AI automatically
    """
    
    def __init__(
        self,
        llm=None,
        max_chunk_size: int = 4000,
        min_chunk_size: int = 500,
        overlap_size: int = 200,
        preserve_code_blocks: bool = True
    ):
        # FIX Issue 3: Log warning for deprecated parameters
        if overlap_size != 200 or not preserve_code_blocks:
            logger.warning(
                "overlap_size and preserve_code_blocks are deprecated in SemanticChunker. "
                "These are handled automatically by the AI pipeline."
            )
        
        if llm is None:
            raise ValueError(
                "SemanticChunker now requires an LLM instance. "
                "Pass llm=your_llm_instance to the constructor."
            )
        super().__init__(llm, max_chunk_size, min_chunk_size)
    
    def chunk(self, document: str, document_id: str = "doc") -> List[SemanticChunk]:
        """
        Synchronous wrapper for backward compatibility.
        
        WARNING: This runs the async pipeline synchronously.
        For better performance, use chunk_with_ai() directly in async code.
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.chunk_with_ai(document, document_id)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.chunk_with_ai(document, document_id)
                )
        except RuntimeError:
            return asyncio.run(self.chunk_with_ai(document, document_id))
