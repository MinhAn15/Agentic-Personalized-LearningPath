from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from backend.models import DocumentInput, LearnerInput, AgentExecutionResponse
from backend.agents import KnowledgeExtractionAgent, ProfilerAgent
from backend.database.database_factory import get_factory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# Global agent instances (will be initialized in main.py)
_knowledge_extraction_agent = None
_profiler_agent = None

def set_agents(ke_agent, p_agent):
    """Set agent instances"""
    global _knowledge_extraction_agent, _profiler_agent
    _knowledge_extraction_agent = ke_agent
    _profiler_agent = p_agent

# ============= KNOWLEDGE EXTRACTION ENDPOINTS =============

@router.post("/knowledge-extraction", response_model=AgentExecutionResponse)
async def extract_knowledge(document: DocumentInput):
    """
    Extract learning concepts from an educational document.
    
    This endpoint:
    1. Parses the document
    2. Extracts key concepts using LLM
    3. Identifies prerequisites
    4. Creates nodes/relationships in Neo4j Course KG
    
    Example request:
    {
        "content": "SQL tutorial content...",
        "document_type": "LECTURE",
        "title": "SQL Basics"
    }
    
    Example response:
    {
        "success": true,
        "agent_type": "knowledge_extraction",
        "execution_time_ms": 2345.5,
        "result": {
            "document_id": "doc_123",
            "concepts_extracted": 8,
            "concepts_created": 8,
            "relationships_created": 5
        }
    }
    """
    try:
        if not _knowledge_extraction_agent:
            raise HTTPException(status_code=500, detail="Knowledge Extraction Agent not initialized")
        
        # Execute agent
        import time
        start_time = time.time()
        
        result = await _knowledge_extraction_agent.execute(
            document_content=document.content,
            document_title=document.title,
            document_type=document.document_type.value if document.document_type else "LECTURE",
            force_real=document.force_real
        )
        
        execution_time = (time.time() - start_time) * 1000  # ms
        
        return AgentExecutionResponse(
            success=result.get("success", False),
            agent_type="knowledge_extraction",
            execution_time_ms=execution_time,
            result=result,
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Knowledge extraction endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= PROFILER ENDPOINTS =============

@router.post("/profiler", response_model=AgentExecutionResponse)
async def profile_learner(learner_input: LearnerInput):
    """
    Create a learner profile from natural language input.
    
    This endpoint:
    1. Parses learner's message
    2. Extracts goal, timeline, learning style
    3. Creates learner profile
    4. Initializes Personal KG
    5. Saves to PostgreSQL
    
    Example request:
    {
        "message": "I want to learn SQL JOINs in 2 weeks. Already know SELECT/FROM.",
        "learner_name": "John"
    }
    
    Example response:
    {
        "success": true,
        "agent_type": "profiler",
        "execution_time_ms": 1234.5,
        "result": {
            "learner_id": "user_abc123",
            "goal": "Master SQL JOINs",
            "time_available": 14,
            "learning_style": "VISUAL"
        }
    }
    """
    try:
        if not _profiler_agent:
            raise HTTPException(status_code=500, detail="Profiler Agent not initialized")
        
        # Execute agent
        import time
        start_time = time.time()
        
        result = await _profiler_agent.execute(
            learner_message=learner_input.message,
            learner_name=learner_input.learner_name or "Learner"
        )
        
        execution_time = (time.time() - start_time) * 1000  # ms
        
        return AgentExecutionResponse(
            success=result.get("success", False),
            agent_type="profiler",
            execution_time_ms=execution_time,
            result=result,
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Profiler endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= HEALTH ENDPOINTS =============

@router.get("/health")
async def agents_health():
    """Check health of all agents"""
    factory = get_factory()
    
    return {
        "agents": {
            "knowledge_extraction": _knowledge_extraction_agent is not None,
            "profiler": _profiler_agent is not None
        },
        "databases": await factory.health_check()
    }
