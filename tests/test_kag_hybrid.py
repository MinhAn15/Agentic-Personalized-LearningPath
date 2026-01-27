import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agents.kag_agent import KAGAgent

@pytest.mark.asyncio
async def test_hybrid_search_execution():
    """
    Verify that _archival_memory_search executes BOTH Vector and Keyword searches
    and combines the results.
    """
    # 1. Setup
    mock_state_manager = MagicMock()
    mock_neo4j = AsyncMock()
    mock_state_manager.neo4j = mock_neo4j
    
    mock_event_bus = MagicMock()
    
    mock_embedding_model = AsyncMock()
    # Mock embedding return
    mock_embedding_model.aget_text_embedding.return_value = [0.1, 0.2, 0.3]
    
    # Initialize Agent with mocks
    agent = KAGAgent(
        "agent-6", 
        state_manager=mock_state_manager, 
        event_bus=mock_event_bus,
        embedding_model=mock_embedding_model
    )
    
    # 2. Mock Neo4j Results
    # We expect 2 calls to run_query: Vector and Keyword.
    # We can distinguish them by the query string.
    
    async def mock_run_query(cypher_sql, **kwargs):
        if "db.index.vector.queryNodes" in cypher_sql:
            # Vector Result
            return [{
                "content": "Vector Result Content",
                "date": "2026-01-01",
                "score": 0.9,
                "source": "vector"
            }]
        elif "CONTAINS $query" in cypher_sql:
            # Keyword Result
            return [{
                "content": "Keyword Result Content",
                "date": "2026-01-02",
                "score": 1.0, 
                "source": "keyword"
            }]
        return []

    mock_neo4j.run_query.side_effect = mock_run_query

    # 3. Execute
    query = "test query"
    result = await agent._archival_memory_search(query)
    
    # 4. Assertions
    print(f"Result: {result}")
    
    # Verify Embedding was called
    mock_embedding_model.aget_text_embedding.assert_called_with(query)
    
    # Verify Neo4j was called at least twice (Vector + Keyword)
    assert mock_neo4j.run_query.call_count >= 2
    
    # Verify Output contains contents from both
    assert "Vector Result Content" in result
    assert "Keyword Result Content" in result
    assert "[VECTOR" in result
    assert "[KEYWORD]" in result
