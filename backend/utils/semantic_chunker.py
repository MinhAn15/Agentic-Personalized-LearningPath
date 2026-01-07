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


# MultiDocFusion (EMNLP 2025) Constants
# Source: Shin et al. (2025) "MultiDocFusion: Hierarchical and Multimodal Chunking Pipeline"
LARGE_DOC_TOKEN_THRESHOLD = 10000  # ~40K chars assuming 4 chars/token
DEFAULT_PARAGRAPH_MIN_CHARS = 100   # Minimum chars for a paragraph to be considered

# Vision Model Constants (Gemini Vision for PDF/Image parsing)
SUPPORTED_VISION_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.pptx'}
VISION_MAX_PAGES = 20  # Max pages to process with vision (to control costs)



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
        min_chunk_size: int = 500,
        vision_llm = None  # NEW: Gemini Vision for PDF/Image parsing (MultiDocFusion)
    ):
        """
        Initialize Agentic Chunker.
        
        Args:
            llm: LLM instance (e.g., Gemini) for reasoning
            max_chunk_size: Soft limit for chunk size (AI will respect this)
            min_chunk_size: Minimum chunk size (AI will merge small chunks)
            vision_llm: Optional Gemini Vision LLM for PDF/Image parsing (MultiDocFusion EMNLP 2025)
        """
        self.llm = llm
        self.vision_llm = vision_llm  # For multimodal document parsing
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.logger = logging.getLogger(f"{__name__}.AgenticChunker")
    
    # ===========================================
    # VISION-BASED PARSING (Gemini Vision)
    # MultiDocFusion Paper: Uses Vision model to parse document structure
    # ===========================================
    
    async def chunk_with_vision(
        self,
        file_path: str,
        document_id: str = "doc",
        document_title: str = "Untitled",
        domain: str = None
    ) -> List[SemanticChunk]:
        """
        Parse document using Gemini Vision for multimodal understanding.
        
        This follows MultiDocFusion (EMNLP 2025) by using Vision model to:
        1. Detect document regions (headings, paragraphs, images, tables)
        2. Extract hierarchical structure from visual layout
        3. Extract text content with proper reading order
        
        Args:
            file_path: Path to PDF/Image/PPT file
            document_id: ID for chunk naming
            document_title: Title for context
            domain: Optional domain hint
            
        Returns:
            List of SemanticChunk objects
        """
        import os
        
        if not self.vision_llm:
            self.logger.warning("Vision LLM not configured, falling back to text extraction")
            return await self._fallback_text_extraction(file_path, document_id, document_title, domain)
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_VISION_EXTENSIONS:
            self.logger.warning(f"Unsupported file type {ext}, falling back to text extraction")
            return await self._fallback_text_extraction(file_path, document_id, document_title, domain)
        
        self.logger.info(f"👁️ [Vision Parser] Processing {file_path} with Gemini Vision")
        
        # Stage 1: Vision model extracts structure + text
        vision_result = await self._vision_parse_document(file_path, document_title, domain)
        
        if not vision_result or not vision_result.get("paragraphs"):
            self.logger.warning("Vision parsing failed, falling back to text extraction")
            return await self._fallback_text_extraction(file_path, document_id, document_title, domain)
        
        paragraphs = vision_result.get("paragraphs", [])
        hierarchy_tree = vision_result.get("hierarchy", {})
        
        self.logger.info(f"📄 [Vision] Extracted {len(paragraphs)} paragraphs with hierarchy")
        
        # If no hierarchy returned, build it with DSHP-LLM
        if not hierarchy_tree or not hierarchy_tree.get("children"):
            hierarchy_tree = await self._dshp_llm_build_tree(paragraphs, document_title, domain)
        
        # Stage 2: DFS Grouping
        grouped_sections = self._dfs_group_tree(hierarchy_tree, paragraphs)
        self.logger.info(f"📦 [DFS] Grouped into {len(grouped_sections)} sections")
        
        # Stage 3: Refiner
        full_text = "\n\n".join(paragraphs)
        refined = await self._refiner_phase(full_text, grouped_sections)
        
        # Stage 4: Executor
        chunks = await self._executor_phase(full_text, refined, document_id)
        self.logger.info(f"✅ [Vision] Created {len(chunks)} semantic chunks")
        
        return chunks
    
    async def _vision_parse_document(
        self,
        file_path: str,
        document_title: str,
        domain: str = None
    ) -> Dict[str, Any]:
        """
        Use Gemini Vision to parse document structure and extract text.
        
        Returns:
            {
                "paragraphs": ["text1", "text2", ...],
                "hierarchy": {"title": "...", "children": [...]}
            }
        """
        import base64
        import os
        
        domain_hint = f"Document Domain: {domain}\n" if domain else ""
        
        # Read file as base64 for Gemini Vision
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            file_base64 = base64.b64encode(file_bytes).decode("utf-8")
        except Exception as e:
            self.logger.error(f"Failed to read file: {e}")
            return {}
        
        ext = os.path.splitext(file_path)[1].lower()
        mime_type = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(ext, "application/pdf")
        
        prompt = f"""You are a document structure analyst using vision to parse this document.

{domain_hint}Document Title: {document_title}

Analyze the visual layout of this document and extract:
1. All text paragraphs in reading order
2. The hierarchical structure (sections, subsections)
3. Identify headings, subheadings based on visual cues (font size, boldness, position)

Return a JSON object:
{{
  "paragraphs": [
    "First paragraph text...",
    "Second paragraph text..."
  ],
  "hierarchy": {{
    "title": "Document Root",
    "level": 0,
    "paragraphs": [],
    "children": [
      {{"title": "Section 1", "level": 1, "paragraphs": [0, 1], "children": []}},
      {{"title": "Section 2", "level": 1, "paragraphs": [2, 3], "children": []}}
    ]
  }}
}}

Rules:
- Extract ALL text content, preserving reading order
- Identify section breaks based on visual layout (spacing, headings)
- Each paragraph index in hierarchy refers to position in paragraphs array
- Keep related content together (concepts with examples)

Return ONLY valid JSON."""

        try:
            # Gemini Vision API call with image/document
            from llama_index.core.llms import ChatMessage, MessageRole
            from llama_index.core.multi_modal_llms import MultiModalLLMMetadata
            
            # Check if vision_llm supports multimodal
            if hasattr(self.vision_llm, 'complete'):
                # For multimodal, we need to pass image data
                # This is a simplified version - actual implementation depends on LlamaIndex version
                response = await self.vision_llm.acomplete(
                    prompt,
                    image_documents=[{"image": file_base64, "mime_type": mime_type}]
                )
            else:
                response = await self.vision_llm.acomplete(prompt)
            
            result = self._parse_json_object(response.text)
            return result if result else {}
            
        except Exception as e:
            self.logger.error(f"Vision parsing error: {e}")
            return {}
    
    async def _fallback_text_extraction(
        self,
        file_path: str,
        document_id: str,
        document_title: str,
        domain: str = None
    ) -> List[SemanticChunk]:
        """
        Fallback: Extract text from file and use standard pipeline.
        """
        import os
        
        ext = os.path.splitext(file_path)[1].lower()
        text = ""
        
        try:
            if ext == ".pdf":
                # Try pymupdf for PDF
                try:
                    import fitz  # pymupdf
                    doc = fitz.open(file_path)
                    text = "\n\n".join([page.get_text() for page in doc])
                    doc.close()
                except ImportError:
                    self.logger.warning("pymupdf not installed, cannot extract PDF text")
            elif ext in {".txt", ".md"}:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            else:
                self.logger.warning(f"Cannot extract text from {ext}")
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
        
        if text:
            return await self.chunk_with_ai(text, document_id, document_title, domain)
        return []
    
    
    async def chunk_with_ai(
        self, 
        document: str, 
        document_id: str = "doc",
        document_title: str = "Untitled",
        domain: str = None  # NEW: Global domain hint for context
    ) -> List[SemanticChunk]:
        """
        Main async chunking method using AI pipeline.
        
        Routes to either:
        - Standard 3-phase pipeline (for small docs <10K tokens)
        - MultiDocFusion pipeline (for large docs >10K tokens)
        
        Args:
            document: Full document text (any format - plain text, markdown, etc.)
            document_id: ID for chunk naming
            document_title: Title for context
            domain: Optional domain/subject hint (e.g., "SQL", "Machine Learning")
            
        Returns:
            List of SemanticChunk objects
        """
        if not document or not document.strip():
            return []
        
        # Estimate token count (simple heuristic: ~4 chars per token)
        estimated_tokens = len(document) // 4
        
        # Route based on document size (MultiDocFusion EMNLP 2025)
        if estimated_tokens > LARGE_DOC_TOKEN_THRESHOLD:
            self.logger.info(
                f"📦 [MultiDocFusion] Large doc detected ({estimated_tokens} est. tokens), "
                f"using hierarchical pipeline for: {document_title}"
            )
            return await self._multidocfusion_pipeline(document, document_id, document_title, domain)
        else:
            self.logger.info(f"🧠 [Agentic Chunker] Standard pipeline for: {document_title}")
            return await self._standard_pipeline(document, document_id, document_title, domain)
    
    async def _standard_pipeline(
        self, 
        document: str, 
        document_id: str, 
        document_title: str,
        domain: str = None
    ) -> List[SemanticChunk]:
        """
        Standard 3-phase pipeline for small/medium documents.
        """
        # Phase 1: Architect - Create logical structure
        structure = await self._architect_phase(document, document_title, domain)
        self.logger.info(f"📐 [Architect] Proposed {len(structure)} sections")
        
        # Phase 2: Refiner - Self-review with Reflexion
        refined_structure = await self._refiner_phase(document, structure)
        self.logger.info(f"🔍 [Refiner] Refined to {len(refined_structure)} sections")
        
        # Phase 3: Executor - Extract chunks based on refined plan
        chunks = await self._executor_phase(document, refined_structure, document_id)
        self.logger.info(f"✅ [Executor] Created {len(chunks)} semantic chunks")
        
        return chunks
    
    # ===========================================
    # MULTIDOCFUSION PIPELINE (EMNLP 2025)
    # Source: Shin et al. (2025) "MultiDocFusion: Hierarchical and Multimodal Chunking"
    # ===========================================
    
    async def _multidocfusion_pipeline(
        self, 
        document: str, 
        document_id: str, 
        document_title: str,
        domain: str = None
    ) -> List[SemanticChunk]:
        """
        MultiDocFusion pipeline for large documents (>10K tokens).
        
        4-Stage Pipeline:
        1. Pre-split: Split by paragraphs (basic heuristic)
        2. DSHP-LLM: LLM reconstructs hierarchical tree from pre-splits
        3. DFS Grouping: Walk tree depth-first, group into chunks
        4. Refinement: Same Refiner phase as standard
        
        Reference: Shin et al. (2025) EMNLP - "MultiDocFusion"
        """
        # Stage 1: Pre-split by paragraphs
        paragraphs = self._paragraph_split(document)
        self.logger.info(f"📄 [Stage 1] Pre-split into {len(paragraphs)} paragraphs")
        
        if len(paragraphs) < 3:
            # Too few paragraphs, fall back to standard
            self.logger.warning("Too few paragraphs, falling back to standard pipeline")
            return await self._standard_pipeline(document, document_id, document_title, domain)
        
        # Stage 2: DSHP-LLM - Hierarchical Tree Reconstruction
        hierarchy_tree = await self._dshp_llm_build_tree(paragraphs, document_title, domain)
        self.logger.info(f"🌳 [Stage 2] Built hierarchical tree")
        
        # Stage 3: DFS Grouping
        grouped_sections = self._dfs_group_tree(hierarchy_tree, paragraphs)
        self.logger.info(f"📦 [Stage 3] DFS grouped into {len(grouped_sections)} sections")
        
        if not grouped_sections:
            # Fallback if tree parsing failed
            self.logger.warning("Tree grouping failed, falling back to standard pipeline")
            return await self._standard_pipeline(document, document_id, document_title, domain)
        
        # Stage 4: Standard Refiner on each group
        refined = await self._refiner_phase(document, grouped_sections)
        self.logger.info(f"🔍 [Stage 4] Refined to {len(refined)} sections")
        
        # Extract chunks
        chunks = await self._executor_phase(document, refined, document_id)
        self.logger.info(f"✅ [MultiDocFusion] Created {len(chunks)} semantic chunks")
        
        return chunks
    
    def _paragraph_split(self, document: str) -> List[str]:
        """
        Stage 1: Pre-split document by paragraphs.
        
        Multi-level fallback strategy for various document formats:
        1. Try double newlines (\\n\\n) - common in plain text
        2. Try single newlines (\\n) - common in OCR/PDF extraction
        3. Try sentence splitting (. ? !) - for continuous text
        4. Fixed-size chunks - last resort for binary/messy text
        """
        paragraphs = []
        
        # === Level 1: Double newline split ===
        raw_paragraphs = document.split('\n\n')
        for para in raw_paragraphs:
            para = para.strip()
            if len(para) >= DEFAULT_PARAGRAPH_MIN_CHARS:
                paragraphs.append(para)
            elif paragraphs and para:
                paragraphs[-1] = paragraphs[-1] + '\n' + para
        
        if len(paragraphs) >= 3:
            self.logger.debug(f"[Pre-split] Level 1 (\\n\\n): {len(paragraphs)} paragraphs")
            return paragraphs
        
        # === Level 2: Single newline split (for PDF/OCR) ===
        paragraphs = []
        raw_paragraphs = document.split('\n')
        current_chunk = ""
        for para in raw_paragraphs:
            para = para.strip()
            if not para:
                if current_chunk:
                    paragraphs.append(current_chunk)
                    current_chunk = ""
            else:
                current_chunk = (current_chunk + "\n" + para).strip() if current_chunk else para
                # Split if chunk is large enough
                if len(current_chunk) >= self.max_chunk_size // 2:
                    paragraphs.append(current_chunk)
                    current_chunk = ""
        if current_chunk:
            paragraphs.append(current_chunk)
        
        if len(paragraphs) >= 3:
            self.logger.debug(f"[Pre-split] Level 2 (\\n): {len(paragraphs)} paragraphs")
            return paragraphs
        
        # === Level 3: Sentence split (for continuous text) ===
        import re
        sentences = re.split(r'(?<=[.!?])\s+', document)
        paragraphs = []
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(current_chunk) + len(sentence) >= self.max_chunk_size // 2:
                if current_chunk:
                    paragraphs.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk = (current_chunk + " " + sentence).strip() if current_chunk else sentence
        if current_chunk:
            paragraphs.append(current_chunk)
        
        if len(paragraphs) >= 3:
            self.logger.debug(f"[Pre-split] Level 3 (sentence): {len(paragraphs)} paragraphs")
            return paragraphs
        
        # === Level 4: Fixed-size chunks (last resort) ===
        chunk_size = self.max_chunk_size // 2  # ~2000 chars
        paragraphs = []
        for i in range(0, len(document), chunk_size):
            chunk = document[i:i + chunk_size].strip()
            if chunk:
                paragraphs.append(chunk)
        
        self.logger.debug(f"[Pre-split] Level 4 (fixed-size): {len(paragraphs)} paragraphs")
        return paragraphs
    
    async def _dshp_llm_build_tree(
        self, 
        paragraphs: List[str], 
        document_title: str,
        domain: str = None
    ) -> Dict[str, Any]:
        """
        Stage 2: DSHP-LLM (Document Section Hierarchical Parsing)
        
        LLM analyzes paragraph summaries and reconstructs a hierarchical tree.
        """
        domain_hint = f"Document Domain: {domain}\n" if domain else ""
        
        # Create paragraph summaries using First 3 Sentences (Discourse Structure Theory)
        # Topic sentences typically appear at the beginning of paragraphs
        import re
        
        def extract_first_sentences(text: str, n: int = 3, max_chars: int = 400) -> str:
            """Extract first N sentences, capped at max_chars for token control."""
            # Split by sentence-ending punctuation
            sentences = re.split(r'(?<=[.!?])\s+', text.strip())
            # Take first N sentences
            first_n = sentences[:n]
            summary = ' '.join(first_n)
            # Cap at max_chars to prevent token overflow
            return summary[:max_chars] + "..." if len(summary) > max_chars else summary
        
        para_list = "\n".join([
            f"[P{i}] {extract_first_sentences(p)}"
            for i, p in enumerate(paragraphs)
        ])
        
        prompt = f"""You are a document structure analyst specializing in educational content.

{domain_hint}Document Title: {document_title}

Paragraphs to organize:
{para_list}

Your task: Build a HIERARCHICAL TREE of this document's logical structure.
Each section should group related paragraphs together.

Return a JSON object with:
- "title": Section title (inferred from content)
- "level": Hierarchy level (0 = root, 1 = top section, 2 = subsection, etc.)
- "paragraphs": List of paragraph indices that belong to this section [0, 1, 2]
- "children": Nested sub-sections (recursive structure)
- "purpose": What this section teaches (1 sentence)
- "chunk_type": One of [CONCEPT_INTRO, EXPLANATION, EXAMPLE, PRACTICE, SUMMARY, MIXED]

Rules:
- Each paragraph should appear in exactly ONE section
- Keep related content together (concepts with their examples)
- Create hierarchy based on topic relationships, not formatting
- Aim for sections that can stand alone as learning units

Example:
{{
  "title": "Document Root",
  "level": 0,
  "paragraphs": [],
  "children": [
    {{"title": "Introduction", "level": 1, "paragraphs": [0, 1], "children": [], "purpose": "Introduces main topic", "chunk_type": "CONCEPT_INTRO"}},
    {{"title": "Core Methods", "level": 1, "paragraphs": [2], "children": [
      {{"title": "Method A", "level": 2, "paragraphs": [3, 4], "children": [], "purpose": "Explains Method A", "chunk_type": "EXPLANATION"}}
    ], "purpose": "Overview of methods", "chunk_type": "MIXED"}}
  ],
  "purpose": "Full document structure",
  "chunk_type": "MIXED"
}}

Return ONLY valid JSON. No explanations."""

        try:
            response = await self.llm.acomplete(prompt)
            tree = self._parse_json_object(response.text)
            return tree if tree else {"title": document_title, "level": 0, "paragraphs": list(range(len(paragraphs))), "children": [], "purpose": "Full document", "chunk_type": "MIXED"}
        except Exception as e:
            self.logger.error(f"DSHP-LLM error: {e}")
            # Fallback: flat structure
            return {
                "title": document_title,
                "level": 0,
                "paragraphs": list(range(len(paragraphs))),
                "children": [],
                "purpose": "Full document",
                "chunk_type": "MIXED"
            }
    
    def _dfs_group_tree(
        self, 
        tree: Dict[str, Any], 
        paragraphs: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Stage 3: DFS traversal to group paragraphs into logical chunks.
        
        Walks the tree depth-first and creates sections from leaf nodes
        or small subtrees.
        """
        sections = []
        
        def traverse(node: Dict, path: List[str] = None):
            if path is None:
                path = []
            
            current_path = path + [node.get("title", "Section")]
            para_indices = node.get("paragraphs", [])
            children = node.get("children", [])
            
            if not children:
                # Leaf node - create a section
                if para_indices:
                    content_parts = [
                        paragraphs[i] for i in para_indices 
                        if i < len(paragraphs)
                    ]
                    if content_parts:
                        full_content = "\n\n".join(content_parts)
                        sections.append({
                            "title": node.get("title", "Section"),
                            "start_text": full_content[:50],
                            "end_text": full_content[-50:] if len(full_content) > 50 else full_content,
                            "purpose": node.get("purpose", ""),
                            "chunk_type": node.get("chunk_type", "MIXED"),
                            "heading_path": current_path
                        })
            else:
                # Non-leaf: If node has direct paragraphs, create section for them
                if para_indices:
                    content_parts = [
                        paragraphs[i] for i in para_indices 
                        if i < len(paragraphs)
                    ]
                    if content_parts:
                        full_content = "\n\n".join(content_parts)
                        sections.append({
                            "title": node.get("title", "Section") + " (Overview)",
                            "start_text": full_content[:50],
                            "end_text": full_content[-50:] if len(full_content) > 50 else full_content,
                            "purpose": node.get("purpose", ""),
                            "chunk_type": node.get("chunk_type", "MIXED"),
                            "heading_path": current_path
                        })
                
                # Recurse into children
                for child in children:
                    traverse(child, current_path)
        
        traverse(tree)
        return sections
    
    def _parse_json_object(self, text: str) -> Dict[str, Any]:
        """Parse JSON object from LLM response."""
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
            if isinstance(result, dict):
                return result
            return {}
        except json.JSONDecodeError:
            # Try to find JSON object in text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {}
    
    async def _architect_phase(
        self, 
        document: str, 
        document_title: str,
        domain: str = None
    ) -> List[Dict[str, Any]]:
        """
        Phase 1: The Architect
        
        LLM analyzes the entire document and creates a logical 
        Table of Contents based on idea flows, regardless of formatting.
        """
        domain_context = f"\nDocument Domain/Subject: {domain}" if domain else ""
        prompt = f"""You are an expert document analyst. Analyze this educational document and identify logical sections based on the FLOW OF IDEAS, not formatting.

Document Title: {document_title}{domain_context}
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
