"""
Unit tests for KAG Agent.

Run: pytest backend/tests/test_kag_agent.py -v
"""

import pytest
from backend.models.artifacts import (
    ArtifactType, AtomicNote, MisconceptionNote, SummaryNote, ArtifactState
)


class TestArtifactModels:
    """Test artifact data models"""
    
    def test_artifact_type_values(self):
        """ArtifactType should have 4 values"""
        assert len(ArtifactType) == 4
        assert ArtifactType.ATOMIC_NOTE.value == "ATOMIC_NOTE"
        assert ArtifactType.MISCONCEPTION_NOTE.value == "MISCONCEPTION_NOTE"
    
    def test_atomic_note_creation(self):
        """AtomicNote should create with defaults"""
        note = AtomicNote(learner_id="l1", concept_id="sql.where")
        
        assert note.learner_id == "l1"
        assert note.concept_id == "sql.where"
        assert note.note_type == ArtifactType.ATOMIC_NOTE
        assert note.note_id.startswith("l1.note.")
        assert note.review_count == 0
    
    def test_atomic_note_to_dict(self):
        """AtomicNote should serialize correctly"""
        note = AtomicNote(learner_id="l1", concept_id="sql.where")
        note.title = "Understanding WHERE"
        note.key_insight = "WHERE filters rows"
        note.tags = ["SQL", "filter"]
        
        d = note.to_dict()
        assert d['title'] == "Understanding WHERE"
        assert d['key_insight'] == "WHERE filters rows"
        assert 'SQL' in d['tags']
    
    def test_misconception_note_creation(self):
        """MisconceptionNote should set correct type"""
        note = MisconceptionNote(
            learner_id="l1",
            concept_id="sql.where",
            misconception_type="where_vs_having"
        )
        
        assert note.note_type == ArtifactType.MISCONCEPTION_NOTE
        assert note.misconception_type == "where_vs_having"
        assert note.severity == "MEDIUM"
    
    def test_artifact_state_tracking(self):
        """ArtifactState should track created artifacts"""
        state = ArtifactState(learner_id="l1")
        
        note = AtomicNote(learner_id="l1", concept_id="sql.where")
        note.title = "Test Note"
        note.content = "This is a test note with some words"
        
        state.add_artifact(note)
        
        assert len(state.created_artifact_ids) == 1
        assert state.artifact_count_by_type['ATOMIC_NOTE'] == 1
        assert state.total_words_created > 0


class TestAtomicNoteGenerator:
    """Test note generation"""
    
    @pytest.mark.asyncio
    async def test_determine_note_type_high_score(self):
        """High score should generate ATOMIC_NOTE"""
        from backend.core.note_generator import AtomicNoteGenerator
        
        generator = AtomicNoteGenerator()
        
        note_type = generator._determine_note_type(
            score=0.85,
            eval_result={'misconceptions': []}
        )
        assert note_type == ArtifactType.ATOMIC_NOTE
    
    @pytest.mark.asyncio
    async def test_determine_note_type_low_score_misconception(self):
        """Low score with misconception should generate MISCONCEPTION_NOTE"""
        from backend.core.note_generator import AtomicNoteGenerator
        
        generator = AtomicNoteGenerator()
        
        note_type = generator._determine_note_type(
            score=0.35,
            eval_result={
                'misconceptions': [{'type': 'conceptual'}],
                'error_type': 'CONCEPTUAL'
            }
        )
        assert note_type == ArtifactType.MISCONCEPTION_NOTE
    
    @pytest.mark.asyncio
    async def test_generate_title(self):
        """Title should be truncated from key insight"""
        from backend.core.note_generator import AtomicNoteGenerator
        
        generator = AtomicNoteGenerator()
        
        long_insight = "This is a very long key insight that should be truncated to fit the title"
        title = generator._generate_title(long_insight, max_length=30)
        
        assert len(title) <= 30
    
    @pytest.mark.asyncio
    async def test_generate_tags(self):
        """Tags should include concept_id"""
        from backend.core.note_generator import AtomicNoteGenerator
        
        generator = AtomicNoteGenerator()
        
        atomic_data = {
            'key_insight': 'WHERE filters rows based on condition',
            'connections': ['sql.select']
        }
        
        tags = await generator._generate_tags(atomic_data, 'sql.where')
        
        assert 'sql.where' in tags
        assert len(tags) <= 10


class TestKGSynchronizer:
    """Test KG synchronization"""
    
    def test_synchronizer_init_no_driver(self):
        """Should initialize without Neo4j driver"""
        from backend.core.kg_synchronizer import KGSynchronizer
        
        syncer = KGSynchronizer(neo4j_driver=None)
        assert syncer.neo4j is None
    
    @pytest.mark.asyncio
    async def test_sync_note_soft_fail_without_driver(self):
        """Should soft-fail if no Neo4j driver"""
        from backend.core.kg_synchronizer import KGSynchronizer
        
        syncer = KGSynchronizer(neo4j_driver=None)
        
        note = {'note_id': 'test', 'concept_id': 'sql.where'}
        result = await syncer.sync_note_to_kg(note, 'learner1')
        
        # Should return True (soft fail)
        assert result == True
    
    @pytest.mark.asyncio
    async def test_link_related_notes_no_driver(self):
        """Should return 0 if no Neo4j driver"""
        from backend.core.kg_synchronizer import KGSynchronizer
        
        syncer = KGSynchronizer(neo4j_driver=None)
        
        result = await syncer.link_related_notes('note1', 'learner1', ['sql.select'])
        assert result == 0


class TestKAGIntegration:
    """Integration tests for KAGAgent"""
    
    def test_kag_init(self):
        """KAGAgent should initialize with core modules"""
        from backend.agents.kag_agent import KAGAgent
        
        class MockStateManager:
            neo4j = None
        
        kag = KAGAgent(
            agent_id="test_kag",
            state_manager=MockStateManager(),
            event_bus=None
        )
        
        assert kag.agent_id == "test_kag"
        assert kag.note_generator is not None
        assert kag.kg_synchronizer is not None
    
    @pytest.mark.asyncio
    async def test_execute_analyze(self):
        """Execute analyze action should work"""
        from backend.agents.kag_agent import KAGAgent
        
        class MockStateManager:
            neo4j = None
        
        kag = KAGAgent(
            agent_id="test_kag",
            state_manager=MockStateManager(),
            event_bus=None
        )
        
        result = await kag.execute(action="analyze", depth="shallow")
        
        # Should return some result (may be error due to no data)
        assert result is not None
