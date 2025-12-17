"""
Atomic Note Generator for KAG Agent.

Per THESIS Section 3.5.5:
- Zettelkasten methodology (atomicity, own words, contextualization, linking)
- LLM-based content generation
- 4 artifact types based on evaluation result
"""

import logging
import json
from typing import Dict, List, Optional

from backend.models.artifacts import (
    AtomicNote, MisconceptionNote, SummaryNote, ArtifactType
)

logger = logging.getLogger(__name__)


class AtomicNoteGenerator:
    """
    Generate Zettelkasten artifacts from evaluation results.
    
    Uses LLM to:
    - Extract key insight (one sentence core understanding)
    - Generate personal example (concrete illustration)
    - Identify common mistakes
    - Find concept connections
    """
    
    def __init__(self, llm_client=None, embedding_model=None, course_kg=None):
        self.llm = llm_client
        self.embeddings = embedding_model
        self.course_kg = course_kg
        self.logger = logging.getLogger(f"{__name__}.AtomicNoteGenerator")
    
    async def generate_note(
        self, 
        learner_id: str, 
        concept_id: str,
        eval_result: Dict, 
        learning_style: str = "VISUAL"
    ) -> Optional[Dict]:
        """
        Generate atomic note from evaluation result.
        
        Returns:
            note_dict with all Zettelkasten fields
        """
        try:
            score = eval_result.get('score', 0.0)
            
            # Step 1: Determine note type
            note_type = self._determine_note_type(score, eval_result)
            
            # Step 2: Generate Zettelkasten content via LLM
            content = await self._generate_zettelkasten_content(
                concept_id, eval_result, learning_style, note_type
            )
            
            # Step 3: Extract atomic components
            atomic_data = self._extract_atomic_components(content)
            
            # Step 4: Generate semantic tags
            tags = await self._generate_tags(atomic_data, concept_id)
            
            # Step 5: Find connections
            connections = await self._find_connections(atomic_data, concept_id)
            
            # Step 6: Create note object
            note = self._create_note_object(
                learner_id, concept_id, atomic_data, 
                tags, connections, note_type, eval_result
            )
            
            self.logger.info(f"Generated {note_type.value} for {learner_id}/{concept_id}")
            return note.to_dict()
        
        except Exception as e:
            self.logger.exception(f"Error generating note: {e}")
            return None
    
    def _determine_note_type(self, score: float, eval_result: Dict) -> ArtifactType:
        """Choose note type based on evaluation"""
        misconceptions = eval_result.get('misconceptions', [])
        error_type = eval_result.get('error_type', 'CORRECT')
        
        if score < 0.5 and (misconceptions or error_type == 'CONCEPTUAL'):
            return ArtifactType.MISCONCEPTION_NOTE
        elif score >= 0.75:
            return ArtifactType.ATOMIC_NOTE
        else:
            return ArtifactType.SUMMARY_NOTE
    
    async def _generate_zettelkasten_content(
        self, 
        concept_id: str,
        eval_result: Dict, 
        learning_style: str, 
        note_type: ArtifactType
    ) -> Dict:
        """Use LLM to generate structured Zettelkasten content"""
        
        # Get concept definition for grounding
        definition = ""
        examples = []
        if self.course_kg:
            concept_node = self.course_kg.get_node(concept_id)
            if concept_node:
                definition = concept_node.get('definition', '')
                examples = concept_node.get('examples', [])[:2]
        
        learner_answer = eval_result.get('learner_answer', '')
        feedback = eval_result.get('feedback_learner', '')
        
        if note_type == ArtifactType.MISCONCEPTION_NOTE:
            prompt = self._build_misconception_prompt(
                concept_id, definition, learner_answer, feedback, learning_style
            )
        else:
            prompt = self._build_atomic_prompt(
                concept_id, definition, examples, learner_answer, feedback, learning_style
            )
        
        if self.llm:
            try:
                response = await self.llm.acomplete(prompt, max_tokens=400)
                response_text = response.text if hasattr(response, 'text') else str(response)
                return self._parse_llm_response(response_text)
            except Exception as e:
                self.logger.warning(f"LLM generation failed: {e}")
        
        # Fallback: create basic structure from available data
        return {
            'KEY_INSIGHT': learner_answer[:200] if learner_answer else f"Understanding of {concept_id}",
            'PERSONAL_EXAMPLE': '',
            'COMMON_MISTAKE': '',
            'CONNECTIONS': []
        }
    
    def _build_atomic_prompt(
        self, concept_id: str, definition: str, examples: list,
        learner_answer: str, feedback: str, learning_style: str
    ) -> str:
        return f"""
Create a Zettelkasten atomic note capturing one learning insight.

Concept: {concept_id}
Definition: {definition}
Examples: {examples}
Learner's answer: {learner_answer}
Feedback: {feedback}
Learning style: {learning_style}

Generate a note with these fields (MUST be valid JSON):
{{
    "KEY_INSIGHT": "The core understanding in 1 sentence",
    "PERSONAL_EXAMPLE": "A concrete {learning_style.lower()} example",
    "COMMON_MISTAKE": "What to avoid",
    "CONNECTIONS": ["related_concept_1", "related_concept_2"],
    "WHY_MATTERS": "Why this insight is important"
}}

Return ONLY valid JSON.
"""
    
    def _build_misconception_prompt(
        self, concept_id: str, definition: str,
        learner_answer: str, feedback: str, learning_style: str
    ) -> str:
        return f"""
Create a Zettelkasten note documenting a learning misconception.

Concept: {concept_id}
Definition: {definition}
Learner's incorrect understanding: {learner_answer}
Feedback: {feedback}

Generate a note with these fields (MUST be valid JSON):
{{
    "KEY_INSIGHT": "Name the misconception clearly",
    "WHAT_LEARNER_THOUGHT": "The incorrect understanding",
    "CORRECT_UNDERSTANDING": "What they should understand",
    "WHY_MISTAKE_COMMON": "Why this misconception occurs",
    "CORRECTION_TIP": "How to remember correctly",
    "CONNECTIONS": ["related_concept_1"]
}}

Return ONLY valid JSON.
"""
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse JSON from LLM response"""
        try:
            # Find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        return {'KEY_INSIGHT': response[:200], 'PERSONAL_EXAMPLE': '', 'COMMON_MISTAKE': ''}
    
    def _extract_atomic_components(self, content: Dict) -> Dict:
        """Extract Zettelkasten atomic components"""
        key_insight = content.get('KEY_INSIGHT', '')
        
        return {
            'title': self._generate_title(key_insight),
            'key_insight': key_insight,
            'personal_example': content.get('PERSONAL_EXAMPLE', ''),
            'common_mistake': content.get('COMMON_MISTAKE', content.get('WHAT_LEARNER_THOUGHT', '')),
            'connections': content.get('CONNECTIONS', []),
            'why_matters': content.get('WHY_MATTERS', '')
        }
    
    def _generate_title(self, key_insight: str, max_length: int = 60) -> str:
        """Generate concise title from key insight"""
        if not key_insight:
            return "Untitled Note"
        return key_insight[:max_length].strip()
    
    async def _generate_tags(self, atomic_data: Dict, concept_id: str) -> List[str]:
        """Generate semantic tags for discoverability"""
        tags = [concept_id]  # Primary tag
        
        # Add connection tags
        connections = atomic_data.get('connections', [])
        if isinstance(connections, str):
            connections = [c.strip() for c in connections.split(',')]
        tags.extend(connections[:3])
        
        # Extract keywords from key_insight
        insight = atomic_data.get('key_insight', '')
        if insight:
            words = insight.split()
            keywords = [w.lower() for w in words if len(w) > 4 and w.isalpha()]
            tags.extend(keywords[:5])
        
        # Deduplicate and limit
        return list(set(tags))[:10]
    
    async def _find_connections(self, atomic_data: Dict, concept_id: str) -> List[str]:
        """Find related concepts to create knowledge network"""
        connections = atomic_data.get('connections', [])
        if isinstance(connections, str):
            connections = [c.strip() for c in connections.split(',')]
        
        # Add prerequisites from Course KG
        if self.course_kg:
            concept_node = self.course_kg.get_node(concept_id)
            if concept_node:
                prerequisites = concept_node.get('prerequisites', [])
                connections.extend(prerequisites[:2])
        
        return list(set(connections))[:5]
    
    def _create_note_object(
        self, 
        learner_id: str, 
        concept_id: str,
        atomic_data: Dict, 
        tags: List[str],
        connections: List[str], 
        note_type: ArtifactType,
        eval_result: Dict
    ) -> AtomicNote:
        """Create note object with all fields"""
        
        if note_type == ArtifactType.MISCONCEPTION_NOTE:
            note = MisconceptionNote(
                learner_id=learner_id,
                concept_id=concept_id,
                misconception_type=atomic_data.get('key_insight', 'unknown')[:100]
            )
            note.severity = 'HIGH' if eval_result.get('score', 0) < 0.3 else 'MEDIUM'
        else:
            note = AtomicNote(
                learner_id=learner_id,
                concept_id=concept_id,
                note_type=note_type
            )
        
        # Set content
        note.title = atomic_data.get('title', '')
        note.key_insight = atomic_data.get('key_insight', '')
        note.personal_example = atomic_data.get('personal_example', '')
        note.common_mistake = atomic_data.get('common_mistake', '')
        note.tags = tags
        note.connections = connections
        
        # Format full content (Markdown)
        note.content = self._format_markdown_content(note, atomic_data)
        
        # Provenance
        note.source_eval_id = eval_result.get('evaluation_id')
        
        return note
    
    def _format_markdown_content(self, note: AtomicNote, atomic_data: Dict) -> str:
        """Format note as Markdown"""
        sections = [f"# {note.title}", "", "## Key Insight", note.key_insight]
        
        if note.personal_example:
            sections.extend(["", "## Example", note.personal_example])
        
        if note.common_mistake:
            sections.extend(["", "## Common Mistake", note.common_mistake])
        
        why_matters = atomic_data.get('why_matters', '')
        if why_matters:
            sections.extend(["", "## Why It Matters", why_matters])
        
        if note.connections:
            sections.extend(["", "## Related Concepts", ", ".join(note.connections)])
        
        if note.tags:
            sections.extend(["", f"**Tags:** {', '.join(note.tags)}"])
        
        return "\n".join(sections)
