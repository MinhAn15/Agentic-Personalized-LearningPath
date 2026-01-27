import os
import asyncio
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "testpassword")
VECTOR_STORE_DIR = Path("backend/storage/vector_store")

async def verify():
    print("Verifying Data Ingestion...")
    
    # 1. Verify Neo4j
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            count_courses = session.run("MATCH (n:Course) RETURN count(n) as count").single()["count"]
            count_concepts = session.run("MATCH (n:Concept) RETURN count(n) as count").single()["count"]
            
            print(f"Neo4j: Found {count_courses} Courses.")
            print(f"Neo4j: Found {count_concepts} Concepts.")
            
            if count_courses == 0 or count_concepts == 0:
                print("Neo4j Verification FAILED.")
            else:
                print("Neo4j Verification PASSED.")
                
        driver.close()
    except Exception as e:
        print(f"Neo4j Verification Error: {e}")

    # 2. Verify Vector Store
    if VECTOR_STORE_DIR.exists():
        files = list(VECTOR_STORE_DIR.glob("*"))
        if len(files) > 0:
             print(f"Vector Store: Found {len(files)} files in {VECTOR_STORE_DIR}.")
        else:
             print("Vector Store: Directory exists but is empty.")
    else:
        print("Vector Store: Directory DOES NOT exist.")

if __name__ == "__main__":
    asyncio.run(verify())
