
import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock

# Adjust path to find backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.kag_agent import KAGAgent

async def test_agent_6_visuals():
    print("🧪 Testing Agent 6: Mermaid Diagram Generation")
    
    # Mock LLM response with Mermaid code
    mock_llm_response = MagicMock()
    mock_llm_response.text = """
    Here is the diagram:
    ```mermaid
    graph TD
      A[Concept] --> B[Insight]
    ```
    """
    
    # Mock LLM
    mock_llm = MagicMock()
    mock_llm.acomplete = AsyncMock(return_value=mock_llm_response)
    
    # Init Agent
    agent = KAGAgent(llm=mock_llm, embedder=MagicMock(), state_manager=MagicMock())
    
    # Test Data
    concept_id = "Polymorphism"
    note_data = {
        "key_insight": "Polymorphism allows objects to modify behavior.",
        "connections": ["Inheritance", "Overriding"]
    }
    
    # 1. Test Direct Generation
    print("\n[1] Testing inner method _generate_concept_map...")
    diagram = await agent._generate_concept_map(concept_id, note_data)
    print(f"Generated Diagram:\n{diagram}")
    
    if "graph TD" in diagram:
        print("✅ Inner method returned valid structure.")
    else:
        print("❌ Inner method failed.")
        
    # 2. Test Integration in extract_atomic_note
    print("\n[2] Testing integration in _extract_atomic_note...")
    
    # Mock the LLM call for the NOTE extraction itself
    mock_note_json = """
    {
        "key_insight": "Polymorphism allows objects to modify behavior.",
        "personal_example": "Like a universal remote.",
        "common_mistake": "Confusing with Overloading.",
        "connections": ["Inheritance"]
    }
    """
    mock_llm_response_note = MagicMock()
    mock_llm_response_note.text = mock_note_json
    
    # Set side_effects: First call (Note), Second call (Diagram)
    mock_llm.acomplete = AsyncMock(side_effect=[mock_llm_response_note, mock_llm_response])
    
    # Create a dummy note type enum
    from enum import Enum
    class NoteType(Enum):
        CONCEPT = "concept"
        
    result = await agent._extract_atomic_note("Polymorphism", "Some content", NoteType.CONCEPT)
    
    content = result["content"]
    print(f"\nFinal Note Content:\n{content}")
    
    if "```mermaid" in content and "graph TD" in content:
        print("✅ Visual Artifact successfully embedded in Note!")
    else:
        print("❌ Visual Artifact MISSING in Note.")

if __name__ == "__main__":
    asyncio.run(test_agent_6_visuals())
