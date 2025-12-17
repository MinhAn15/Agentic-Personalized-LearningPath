import logging
import uuid
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from statistics import mean, stdev
from enum import Enum

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.note_generator import AtomicNoteGenerator
from backend.core.kg_synchronizer import KGSynchronizer
from backend.models.artifacts import (
    ArtifactType, AtomicNote, MisconceptionNote, ArtifactState
)
from backend.config import get_settings
from llama_index.llms.gemini import Gemini

logger = logging.getLogger(__name__)


# ArtifactType imported from backend.models.artifacts


class KAGAgent(BaseAgent):
    """
    KAG Agent - Knowledge Graph Aggregator (per Thesis).
    
    Features:
    1. Zettelkasten Artifact Generation
       - Extract Atomic Notes (Definition + Personal Example)
       - Generate Links (Connect to related notes)
       - Create Tags (Semantic tags for retrieval)
       - Store as NoteNode in Neo4j Personal Graph
    
    2. Dual-KG Synchronization
       - Course KG (Read-only): Reference point
       - Personal KG (Read-Write):
         * LearnerNode -> HAS_MASTERY -> ConceptNode
         * LearnerNode -> HAS_MISCONCEPTION -> ErrorNode
         * LearnerNode -> CREATED_NOTE -> NoteNode
    
    3. System Learning (Pattern Recognition)
       - Aggregate error patterns from all learners
       - Identify Bottleneck Concepts (high failure rate)
       - Recommend content improvements
    
    Process Flow:
    1. Trigger: After successful Tutor/Evaluator session
    2. Extract Atomic Note from session
    3. Find related notes via semantic similarity
    4. Create NoteNode with links in Personal KG
    5. Update aggregated statistics
    6. Generate recommendations for course improvement
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus, llm=None,
                 embedding_model=None, course_kg=None):
        super().__init__(agent_id, AgentType.KAG, state_manager, event_bus)
        
        self.settings = get_settings()
        self.llm = llm or Gemini(
            model=self.settings.GEMINI_MODEL,
            api_key=self.settings.GOOGLE_API_KEY
        )
        self.logger = logging.getLogger(f"KAGAgent.{agent_id}")
        
        # Store references
        self.course_kg = course_kg
        
        # Initialize core modules
        self.note_generator = AtomicNoteGenerator(
            llm_client=self.llm,
            embedding_model=embedding_model,
            course_kg=course_kg
        )
        self.kg_synchronizer = KGSynchronizer(
            neo4j_driver=state_manager.neo4j if state_manager else None
        )
        
        # Event subscriptions
        if event_bus and hasattr(event_bus, 'subscribe'):
            event_bus.subscribe('EVALUATION_COMPLETED', self._on_evaluation_completed)
            self.logger.info("Subscribed to EVALUATION_COMPLETED")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Main execution method."""
        try:
            action = kwargs.get("action", "analyze")
            
            if action == "generate_artifact":
                return await self._generate_artifact(**kwargs)
            elif action == "analyze":
                return await self._analyze_system(**kwargs)
            elif action == "sync_kg":
                return await self._sync_dual_kg(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "agent_id": self.agent_id
                }
        
        except Exception as e:
            self.logger.error(f"❌ KAG execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    # ==========================================
    # 1. ZETTELKASTEN ARTIFACT GENERATION
    # ==========================================
    
    async def _generate_artifact(self, **kwargs) -> Dict[str, Any]:
        """
        Generate Zettelkasten artifact from learning session.
        
        Args:
            learner_id: str
            concept_id: str
            session_data: Dict with question, answer, feedback, etc.
        """
        learner_id = kwargs.get("learner_id")
        concept_id = kwargs.get("concept_id")
        session_data = kwargs.get("session_data", {})
        
        if not all([learner_id, concept_id]):
            return {
                "success": False,
                "error": "learner_id and concept_id required"
            }
        
        self.logger.info(f"📝 Generating artifact for {learner_id} on {concept_id}")
        
        # Step 1: Extract Atomic Note
        atomic_note = await self._extract_atomic_note(
            concept_id=concept_id,
            session_data=session_data
        )
        
        # Step 2: Find related notes
        related_notes = await self._find_related_notes(
            learner_id=learner_id,
            atomic_note=atomic_note
        )
        
        # Step 3: Generate semantic tags
        tags = await self._generate_tags(atomic_note)
        
        # Step 4: Create NoteNode in Personal KG
        note_id = await self._create_note_node(
            learner_id=learner_id,
            concept_id=concept_id,
            atomic_note=atomic_note,
            related_notes=related_notes,
            tags=tags
        )
        
        # Step 5: Create links to related notes
        await self._create_note_links(note_id, related_notes)
        
        result = {
            "success": True,
            "agent_id": self.agent_id,
            "note_id": note_id,
            "artifact_type": atomic_note["type"],
            "content_preview": atomic_note["content"][:100] + "...",
            "related_notes": len(related_notes),
            "tags": tags,
            "timestamp": datetime.now().isoformat()
        }
        
        # Emit event
        await self.send_message(
            receiver="profiler",
            message_type="artifact_created",
            payload={
                "learner_id": learner_id,
                "concept_id": concept_id,
                "note_id": note_id
            }
        )
        
        self.logger.info(f"✅ Artifact created: {note_id}")
        
        return result
    
    async def _extract_atomic_note(
        self, concept_id: str, session_data: Dict
    ) -> Dict[str, Any]:
        """Extract atomic note from session data"""
        
        question = session_data.get("question", "")
        answer = session_data.get("answer", "")
        feedback = session_data.get("feedback", "")
        score = session_data.get("score", 0)
        
        # Determine note type
        if score < 0.5:
            note_type = ArtifactType.MISCONCEPTION_NOTE
        else:
            note_type = ArtifactType.ATOMIC_NOTE
        
        # Generate atomic note content using LLM
        prompt = f"""
Create a concise learning note (Zettelkasten style) from this learning interaction.

Concept: {concept_id}
Question: {question}
Learner's Answer: {answer}
Feedback: {feedback}
Score: {score}

Generate a note with:
1. KEY_INSIGHT: One sentence capturing the core understanding
2. PERSONAL_EXAMPLE: A concrete example showing understanding
3. COMMON_MISTAKE: What to avoid (if applicable)
4. CONNECTIONS: Related concepts to link

Return ONLY valid JSON:
{{
  "key_insight": "...",
  "personal_example": "...",
  "common_mistake": "...",
  "connections": ["concept1", "concept2"]
}}
"""
        
        response = await self.llm.acomplete(prompt)
        response_text = response.text
        
        try:
            import json
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                note_data = json.loads(response_text[json_start:json_end])
            else:
                note_data = {
                    "key_insight": f"Learning about {concept_id}",
                    "personal_example": answer[:200] if answer else "",
                    "common_mistake": "",
                    "connections": []
                }
        except:
            note_data = {
                "key_insight": f"Learning about {concept_id}",
                "personal_example": answer[:200] if answer else "",
                "common_mistake": "",
                "connections": []
            }
        
        # Build atomic note
        content = f"""
# {concept_id}

## Key Insight
{note_data.get('key_insight', '')}

## Personal Example
{note_data.get('personal_example', '')}

## Common Mistake
{note_data.get('common_mistake', '')}
""".strip()
        
        return {
            "type": note_type.value,
            "content": content,
            "key_insight": note_data.get("key_insight", ""),
            "personal_example": note_data.get("personal_example", ""),
            "common_mistake": note_data.get("common_mistake", ""),
            "connections": note_data.get("connections", []),
            "concept_id": concept_id
        }
    
    async def _find_related_notes(
        self, learner_id: str, atomic_note: Dict
    ) -> List[Dict[str, Any]]:
        """Find related notes in learner's Personal KG"""
        neo4j = self.state_manager.neo4j
        
        # Find notes with similar tags or connected concepts
        connections = atomic_note.get("connections", [])
        
        if not connections:
            return []
        
        result = await neo4j.run_query(
            """
            MATCH (l:Learner {learner_id: $learner_id})-[:CREATED_NOTE]->(n:NoteNode)
            WHERE n.concept_id IN $connections
               OR any(tag IN n.tags WHERE tag IN $connections)
            RETURN n.note_id as note_id,
                   n.concept_id as concept_id,
                   n.key_insight as key_insight
            LIMIT 5
            """,
            learner_id=learner_id,
            connections=connections
        )
        
        return result if result else []
    
    async def _generate_tags(self, atomic_note: Dict) -> List[str]:
        """Generate semantic tags for the note"""
        tags = []
        
        # Add concept ID as primary tag
        tags.append(atomic_note.get("concept_id", ""))
        
        # Add connections as tags
        tags.extend(atomic_note.get("connections", []))
        
        # Add type-based tag
        tags.append(atomic_note.get("type", "").lower())
        
        # Generate additional tags from content
        key_words = atomic_note.get("key_insight", "").split()[:5]
        tags.extend([w.lower() for w in key_words if len(w) > 3])
        
        # Deduplicate and clean
        return list(set([t for t in tags if t]))[:10]
    
    async def _create_note_node(
        self,
        learner_id: str,
        concept_id: str,
        atomic_note: Dict,
        related_notes: List[Dict],
        tags: List[str]
    ) -> str:
        """Create NoteNode in Personal KG"""
        note_id = f"note_{uuid.uuid4().hex[:8]}"
        neo4j = self.state_manager.neo4j
        
        await neo4j.run_query(
            """
            MATCH (l:Learner {learner_id: $learner_id})
            CREATE (n:NoteNode {
                note_id: $note_id,
                concept_id: $concept_id,
                type: $type,
                content: $content,
                key_insight: $key_insight,
                personal_example: $personal_example,
                common_mistake: $common_mistake,
                tags: $tags,
                created_at: datetime()
            })
            CREATE (l)-[:CREATED_NOTE]->(n)
            WITH n
            MATCH (c:CourseConcept {concept_id: $concept_id})
            CREATE (n)-[:ABOUT]->(c)
            """,
            learner_id=learner_id,
            note_id=note_id,
            concept_id=concept_id,
            type=atomic_note["type"],
            content=atomic_note["content"],
            key_insight=atomic_note.get("key_insight", ""),
            personal_example=atomic_note.get("personal_example", ""),
            common_mistake=atomic_note.get("common_mistake", ""),
            tags=tags
        )
        
        return note_id
    
    async def _create_note_links(
        self, note_id: str, related_notes: List[Dict]
    ) -> None:
        """Create links between notes"""
        neo4j = self.state_manager.neo4j
        
        for related in related_notes:
            related_id = related.get("note_id")
            if related_id:
                await neo4j.run_query(
                    """
                    MATCH (n1:NoteNode {note_id: $note_id})
                    MATCH (n2:NoteNode {note_id: $related_id})
                    MERGE (n1)-[:LINKS_TO]->(n2)
                    """,
                    note_id=note_id,
                    related_id=related_id
                )
    
    # ==========================================
    # 2. DUAL-KG SYNCHRONIZATION
    # ==========================================
    
    async def _sync_dual_kg(self, **kwargs) -> Dict[str, Any]:
        """
        Synchronize Personal KG with Course KG updates.
        
        - Course KG: Read-only reference
        - Personal KG: Update mastery, misconceptions, notes
        """
        learner_id = kwargs.get("learner_id")
        updates = kwargs.get("updates", {})
        
        if not learner_id:
            return {"success": False, "error": "learner_id required"}
        
        self.logger.info(f"🔄 Syncing Personal KG for {learner_id}")
        
        neo4j = self.state_manager.neo4j
        sync_count = 0
        
        # Sync mastery levels
        mastery_updates = updates.get("mastery", {})
        for concept_id, level in mastery_updates.items():
            await neo4j.run_query(
                """
                MATCH (l:Learner {learner_id: $learner_id})
                MATCH (c:CourseConcept {concept_id: $concept_id})
                MERGE (l)-[m:HAS_MASTERY]->(c)
                SET m.level = $level, m.updated_at = datetime()
                """,
                learner_id=learner_id,
                concept_id=concept_id,
                level=level
            )
            sync_count += 1
        
        # Sync misconceptions
        misconceptions = updates.get("misconceptions", [])
        for misconception in misconceptions:
            error_id = f"error_{uuid.uuid4().hex[:8]}"
            await neo4j.run_query(
                """
                MATCH (l:Learner {learner_id: $learner_id})
                MATCH (c:CourseConcept {concept_id: $concept_id})
                CREATE (e:ErrorNode {
                    error_id: $error_id,
                    description: $description,
                    error_type: $error_type,
                    created_at: datetime()
                })
                CREATE (l)-[:HAS_MISCONCEPTION]->(e)
                CREATE (e)-[:ABOUT]->(c)
                """,
                learner_id=learner_id,
                concept_id=misconception.get("concept_id"),
                error_id=error_id,
                description=misconception.get("description", ""),
                error_type=misconception.get("error_type", "CONCEPTUAL")
            )
            sync_count += 1
        
        return {
            "success": True,
            "agent_id": self.agent_id,
            "learner_id": learner_id,
            "sync_count": sync_count,
            "timestamp": datetime.now().isoformat()
        }
    
    # ==========================================
    # 3. SYSTEM LEARNING & ANALYSIS
    # ==========================================
    
    async def _analyze_system(self, **kwargs) -> Dict[str, Any]:
        """
        Analyze aggregated learner patterns.
        
        - Retrieve all learner Personal KGs
        - Calculate statistics
        - Identify bottleneck concepts
        - Generate recommendations
        """
        analysis_depth = kwargs.get("analysis_depth", "shallow")
        min_learners = kwargs.get("min_learners", 5)
        
        self.logger.info(f"📊 Starting KAG analysis (depth={analysis_depth})")
        
        # Step 1: Get all learner graphs
        learner_graphs = await self._retrieve_all_learner_graphs()
        
        if len(learner_graphs) < min_learners:
            return {
                "success": False,
                "error": f"Need at least {min_learners} learners, found {len(learner_graphs)}",
                "agent_id": self.agent_id
            }
        
        self.logger.info(f"Retrieved {len(learner_graphs)} learner graphs")
        
        # Step 2: Merge into aggregated view
        aggregated_graph = await self._merge_graphs(learner_graphs)
        
        # Step 3: Calculate statistics
        statistics = await self._calculate_statistics(aggregated_graph)
        
        # Step 4: Identify patterns
        patterns = await self._identify_patterns(
            aggregated_graph=aggregated_graph,
            statistics=statistics,
            depth=analysis_depth
        )
        
        # Step 5: Generate insights and recommendations
        insights = patterns.get("insights", [])
        recommendations = await self._generate_recommendations(patterns)
        predictions = await self._predict_interventions(patterns)
        
        result = {
            "success": True,
            "agent_id": self.agent_id,
            "num_learners_analyzed": len(learner_graphs),
            "statistics": statistics,
            "patterns": patterns,
            "insights": insights,
            "recommendations": recommendations,
            "predictions": predictions,
            "timestamp": datetime.now().isoformat()
        }
        
        # Emit event for course improvement
        await self.send_message(
            receiver="knowledge_extraction",
            message_type="kag_analysis_complete",
            payload={
                "recommendations": recommendations,
                "bottleneck_concepts": patterns.get("difficult_concepts", [])
            }
        )
        
        self.logger.info(f"✅ KAG analysis complete: {len(insights)} insights")
        
        return result
    
    async def _retrieve_all_learner_graphs(self) -> List[Dict[str, Any]]:
        """Retrieve all learner Personal KGs"""
        neo4j = self.state_manager.neo4j
        
        result = await neo4j.run_query(
            """
            MATCH (l:Learner)-[m:HAS_MASTERY]->(c:CourseConcept)
            RETURN l.learner_id as learner_id,
                   collect({concept_id: c.concept_id, mastery: m.level}) as masteries
            """
        )
        
        if result:
            learner_graphs = []
            for row in result:
                graph = {row["learner_id"]: {}}
                for mastery in row.get("masteries", []):
                    graph[row["learner_id"]][mastery["concept_id"]] = mastery["mastery"]
                learner_graphs.append(graph)
            return learner_graphs
        
        return []
    
    async def _merge_graphs(self, learner_graphs: List[Dict]) -> Dict[str, Any]:
        """Merge all learner graphs into aggregated view"""
        aggregated = {"concepts": {}}
        
        for learner_graph in learner_graphs:
            for learner_id, masteries in learner_graph.items():
                for concept_id, mastery in masteries.items():
                    if concept_id not in aggregated["concepts"]:
                        aggregated["concepts"][concept_id] = {
                            "masteries": [],
                            "errors": [],
                            "misconceptions": []
                        }
                    
                    aggregated["concepts"][concept_id]["masteries"].append(mastery)
        
        return aggregated
    
    async def _calculate_statistics(self, aggregated: Dict) -> Dict[str, Any]:
        """Calculate statistics across all learners"""
        statistics = {}
        
        for concept_id, data in aggregated.get("concepts", {}).items():
            masteries = data.get("masteries", [])
            
            if masteries:
                statistics[concept_id] = {
                    "avg_mastery": mean(masteries),
                    "std_dev": stdev(masteries) if len(masteries) > 1 else 0,
                    "min_mastery": min(masteries),
                    "max_mastery": max(masteries),
                    "num_learners": len(masteries),
                    "struggle_rate": len([m for m in masteries if m < 0.5]) / len(masteries)
                }
        
        return statistics
    
    async def _identify_patterns(
        self,
        aggregated_graph: Dict,
        statistics: Dict,
        depth: str = "shallow"
    ) -> Dict[str, Any]:
        """Identify patterns and bottlenecks"""
        patterns = {
            "difficult_concepts": [],
            "easy_concepts": [],
            "misconception_clusters": {},
            "prerequisite_impacts": {},
            "insights": []
        }
        
        for concept_id, stats in statistics.items():
            avg_mastery = stats.get("avg_mastery", 0)
            struggle_rate = stats.get("struggle_rate", 0)
            
            if avg_mastery < 0.4:
                patterns["difficult_concepts"].append({
                    "concept_id": concept_id,
                    "avg_mastery": avg_mastery,
                    "struggle_rate": struggle_rate
                })
                patterns["insights"].append(
                    f"⚠️ {concept_id}: Only {avg_mastery:.0%} mastery, "
                    f"{struggle_rate:.0%} struggle"
                )
            
            elif avg_mastery > 0.8:
                patterns["easy_concepts"].append({
                    "concept_id": concept_id,
                    "avg_mastery": avg_mastery
                })
        
        # Deep analysis: prerequisite impact
        if depth == "deep":
            patterns["prerequisite_impacts"] = await self._analyze_prerequisite_impact(
                patterns["difficult_concepts"]
            )
        
        return patterns
    
    async def _analyze_prerequisite_impact(
        self, difficult_concepts: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze how prerequisites affect difficult concepts"""
        neo4j = self.state_manager.neo4j
        impacts = {}
        
        for concept in difficult_concepts:
            concept_id = concept["concept_id"]
            
            result = await neo4j.run_query(
                """
                MATCH (c:CourseConcept {concept_id: $concept_id})-[:REQUIRES]->(prereq)
                MATCH (l:Learner)-[m:HAS_MASTERY]->(prereq)
                RETURN prereq.concept_id as prereq_id,
                       avg(m.level) as avg_prereq_mastery
                """,
                concept_id=concept_id
            )
            
            if result:
                impacts[concept_id] = [
                    {"prereq": r["prereq_id"], "avg_mastery": r["avg_prereq_mastery"]}
                    for r in result
                ]
        
        return impacts
    
    async def _generate_recommendations(self, patterns: Dict) -> List[str]:
        """Generate course improvement recommendations"""
        recommendations = []
        
        for difficult in patterns.get("difficult_concepts", []):
            concept_id = difficult.get("concept_id")
            struggle_rate = difficult.get("struggle_rate", 0)
            
            if struggle_rate > 0.6:
                recommendations.append(
                    f"📚 PRIORITY: Strengthen {concept_id} prerequisites - {struggle_rate:.0%} struggle rate"
                )
                recommendations.append(
                    f"📝 Create comparison tutorial: {concept_id} vs similar concepts"
                )
                recommendations.append(
                    f"🎯 Add interactive practice exercises for {concept_id}"
                )
            elif struggle_rate > 0.3:
                recommendations.append(
                    f"📖 Add more examples for {concept_id}"
                )
        
        return recommendations
    
    async def _predict_interventions(self, patterns: Dict) -> List[str]:
        """Predict intervention points for future learners"""
        predictions = []
        
        for difficult in patterns.get("difficult_concepts", []):
            concept_id = difficult.get("concept_id")
            predictions.append(
                f"🚀 Next cohort: Allocate 2x time for {concept_id}"
            )
            predictions.append(
                f"🚩 Flag learners struggling with {concept_id} prerequisites early"
            )
        
        return predictions
    
    # ==========================================
    # EVENT HANDLERS (Per THESIS Integration)
    # ==========================================
    
    async def _on_evaluation_completed(self, event: Dict):
        """
        Handle EVALUATION_COMPLETED event from Evaluator Agent.
        
        Auto-generates Zettelkasten artifact based on evaluation result.
        
        Event payload:
        {
            'learner_id': str,
            'concept_id': str,
            'score': float,
            'error_type': str,
            'misconceptions': list,
            'mastery_after': float
        }
        """
        try:
            learner_id = event.get('learner_id')
            concept_id = event.get('concept_id')
            
            if not learner_id or not concept_id:
                self.logger.warning("Missing learner_id or concept_id in event")
                return
            
            self.logger.info(f"EVALUATION_COMPLETED: Generating artifact for {learner_id}/{concept_id}")
            
            # Get learner profile for learning style
            profile = await self.state_manager.get_state(learner_id, 'LearnerProfile') if self.state_manager else {}
            learning_style = profile.get('learning_style', 'VISUAL') if profile else 'VISUAL'
            
            # Generate artifact using note generator
            note_dict = await self.note_generator.generate_note(
                learner_id=learner_id,
                concept_id=concept_id,
                eval_result=event,
                learning_style=learning_style
            )
            
            if not note_dict:
                self.logger.warning("Note generation failed")
                return
            
            # Sync to Personal KG
            sync_success = await self.kg_synchronizer.sync_note_to_kg(note_dict, learner_id)
            
            if sync_success:
                # Link related notes
                connections = note_dict.get('connections', [])
                links_created = await self.kg_synchronizer.link_related_notes(
                    note_dict['note_id'], learner_id, connections
                )
                
                # Update mastery node
                await self.kg_synchronizer.update_mastery_node(
                    learner_id, concept_id,
                    event.get('mastery_after', 0.0),
                    'APPLY'  # Default Bloom level
                )
                
                # Emit ARTIFACT_CREATED event
                if self.event_bus:
                    await self.event_bus.publish('ARTIFACT_CREATED', {
                        'learner_id': learner_id,
                        'concept_id': concept_id,
                        'note_id': note_dict['note_id'],
                        'artifact_type': note_dict['type'],
                        'links_created': links_created
                    })
                
                self.logger.info(f"Created artifact {note_dict['note_id']} with {links_created} links")
        
        except Exception as e:
            self.logger.exception(f"Error handling EVALUATION_COMPLETED: {e}")

