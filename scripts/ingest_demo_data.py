import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Use backend imports
import sys
# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Document,
    Settings
)
from llama_index.core.node_parser import SentenceSplitter
from backend.core.llm_factory import LLMFactory
from backend.config import get_settings
from neo4j import AsyncGraphDatabase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Constants
DEMO_DATA_DIR = Path("demo_data")
VECTOR_STORE_DIR = Path("backend/storage/vector_store")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "testpassword")

async def setup_neo4j_driver():
    return AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

import time

async def ingest_to_vector_store(documents: List[Document]):
    """Ingest documents into Vector Store with Rate Limiting."""
    logger.info(f"📚 Processing {len(documents)} documents for Vector Store...")
    
    settings = get_settings()
    
    # Configure Embeddings explicitly using Factory
    try:
        Settings.embed_model = LLMFactory.get_embedding_model()
        logger.info(f"Using Embedding Model: {Settings.embed_model.class_name()}")
    except Exception as e:
        logger.warning(f"Failed to load embedding model via Factory: {e}. LlamaIndex might default to OpenAI.")

    # Always initialize index first
    if not VECTOR_STORE_DIR.exists():
        logger.info("Initializing new Vector Store (Empty)...")
        # Create empty index first to avoid massive initial embedding call
        index = VectorStoreIndex.from_documents([], show_progress=True)
        index.storage_context.persist(persist_dir=str(VECTOR_STORE_DIR))
    else:
        logger.info("Loading existing Vector Store...")
        storage_context = StorageContext.from_defaults(persist_dir=str(VECTOR_STORE_DIR))
        index = load_index_from_storage(storage_context)

    # Process documents in small batches with delay
    BATCH_SIZE = 1
    DELAY_SECONDS = 2
    
    total_docs = len(documents)
    logger.info(f"Insering {total_docs} docs in batches of {BATCH_SIZE} with {DELAY_SECONDS}s delay...")
    
    for i in range(0, total_docs, BATCH_SIZE):
        batch = documents[i:i + BATCH_SIZE]
        logger.info(f"  Embedding batch {i//BATCH_SIZE + 1}/{(total_docs + BATCH_SIZE - 1)//BATCH_SIZE}...")
        
        try:
            for doc in batch:
                index.insert(doc)
            
            # Save progress periodically
            if (i + BATCH_SIZE) % 5 == 0:
                 index.storage_context.persist(persist_dir=str(VECTOR_STORE_DIR))
                 
            time.sleep(DELAY_SECONDS)
            
        except Exception as e:
            logger.error(f"  ❌ Failed to insert batch starting at index {i}: {e}")
            # Continue to next batch? Maybe stop? Let's verify connection first.
            if "quota" in str(e).lower():
                logger.warning("  ⚠️ Quota exceeded. Waiting 60 seconds...")
                time.sleep(60)
                # Retry current batch logic would be better, but keeping it simple for now: skip
    
    # Final Persist
    index.storage_context.persist(persist_dir=str(VECTOR_STORE_DIR))
        
    logger.info("✅ Vector Store Updated.")

async def ingest_to_graph(driver, documents: List[Document]):
    """Ingest inferred logical structure into Neo4j."""
    logger.info("🕸️  Ingesting to Knowledge Graph (Neo4j)...")
    
    # Process courses (subdirectories) and concepts (files)
    # Heuristic: 
    #   Subdir Name -> Course Name
    #   File Name -> Concept Name
    
    courses_data = {}
    
    for doc in documents:
        file_path = Path(doc.metadata.get('file_path'))
        
        # Get relative path from DEMO_DATA_DIR to determine structure
        try:
            rel_path = file_path.relative_to(DEMO_DATA_DIR.resolve())
        except ValueError:
             # Fallback if resolve issues or running from different cwd
             rel_path = file_path
             if "demo_data" in str(file_path):
                 parts = file_path.parts
                 idx = parts.index("demo_data")
                 rel_path = Path(*parts[idx+1:])

        if len(rel_path.parts) > 1:
            course_name = rel_path.parts[0]
            concept_name = rel_path.stem
            
            if course_name not in courses_data:
                courses_data[course_name] = []
            
            courses_data[course_name].append({
                "name": concept_name,
                "file_path": str(file_path)
            })
            
    # Cypher Queries
    create_course_query = """
    MERGE (c:Course {id: $course_id})
    SET c.name = $course_name
    RETURN c
    """
    
    create_concept_query = """
    MATCH (c:Course {id: $course_id})
    MERGE (n:Concept {id: $concept_id})
    SET n.name = $concept_name, n.file_path = $file_path
    MERGE (c)-[:HAS_CONCEPT]->(n)
    """
    
    async with driver.session() as session:
        for course_name, concepts in courses_data.items():
            course_id = course_name.lower().replace(" ", "_")
            logger.info(f"  > Processing Course: {course_name}")
            
            await session.run(create_course_query, course_id=course_id, course_name=course_name)
            
            for concept in concepts:
                concept_id = concept["name"].lower().replace(" ", "_")
                await session.run(create_concept_query, 
                                  course_id=course_id,
                                  concept_id=concept_id,
                                  concept_name=concept["name"],
                                  file_path=concept["file_path"])
                
    logger.info("✅ Knowledge Graph Ingested.")

async def main():
    print("Starting Data Ingestion...")
    
    # 1. Load Documents
    target_dir = DEMO_DATA_DIR
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
        
    if not target_dir.exists():
        logger.error(f"Target directory not found at {target_dir.absolute()}")
        return

    logger.info(f"📂 Loading documents from: {target_dir}")
    reader = SimpleDirectoryReader(str(target_dir), recursive=True)
    documents = reader.load_data()
    logger.info(f"Loaded {len(documents)} document chunks.")
    
    # 2. Vector Store Ingestion
    try:
        await ingest_to_vector_store(documents)
    except Exception as e:
        logger.error(f"Vector Store Ingestion Failed: {e}")
        # Proceed to Graph anyway? Better to fail? Let's try Graph.
        
    # 3. Knowledge Graph Ingestion
    try:
        driver = await setup_neo4j_driver()
        await ingest_to_graph(driver, documents)
        await driver.close()
    except Exception as e:
        logger.error(f"Knowledge Graph Ingestion Failed: {e}")

    print("Data Ingestion Complete!")

if __name__ == "__main__":
    asyncio.run(main())
