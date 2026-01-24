import os
import asyncio
from neo4j import GraphDatabase
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "testpassword")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/learning_db")

DEMO_USER_EMAIL = "demo@example.com"
DEMO_USERNAME = "demo_learner"

async def reset_postgres():
    print(f"🔄 Cleaning PostgreSQL for user: {DEMO_USERNAME}...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        # Delete user if exists (cascade should handle sessions/progress)
        await conn.execute("DELETE FROM users WHERE email = $1", DEMO_USER_EMAIL)
        await conn.close()
        print("✅ PostgreSQL clean.")
    except asyncpg.UndefinedTableError:
        print("⚠️  PostgreSQL: Table 'users' does not exist yet. Configuring environment...")
        # This is fine, it means the backend hasn't created tables yet.
        # The demo will run fine as tables will be created on first API reques/startup.
    except Exception as e:
        print(f"❌ PostgreSQL Error: {e}")

def reset_neo4j():
    print(f"🔄 Cleaning Neo4j for user: {DEMO_USERNAME}...")
    max_retries = 30
    import time
    
    for i in range(max_retries):
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            with driver.session() as session:
                # Test connection first
                session.run("RETURN 1")
                
                query = """
                MATCH (l:Learner {email: $email})
                OPTIONAL MATCH (l)-[:HAS_MASTERY]->(m:MasteryNode)
                DETACH DELETE l, m
                """
                session.run(query, email=DEMO_USER_EMAIL)
            print("✅ Neo4j clean.")
            driver.close()
            return
        except Exception as e:
            if i < max_retries - 1:
                print(f"⏳ Neo4j starting up... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print(f"❌ Neo4j Error after retries: {e}")

async def main():
    print("🎬 APLO Demo Reset Tool 🎬")
    print("---------------------------")
    await reset_postgres()
    reset_neo4j()
    print("---------------------------")
    print("✨ Environment Ready for Recording!")
    print(f"You can now Sign Up as '{DEMO_USERNAME}' ({DEMO_USER_EMAIL})")

if __name__ == "__main__":
    asyncio.run(main())
