import asyncio
import logging
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import get_settings
import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PilotSmokeTest")

client = TestClient(app)

def test_learner_signup_flow():
    """
    Smoke Test: Verify Learner Signup, Consent, and Experiment Assignment.
    """
    logger.info("🚀 Starting Pilot Onboarding Smoke Test...")

    # 1. Payload
    payload = {
        "name": "Pilot Tester",
        "email": "pilot.tester@example.com",
        "age": 25,
        "background": "Student",
        "consent_agreed": True
    }

    # 2. Call API
    logger.info("📡 Sending Signup Request...")
    response = client.post("/api/v1/learners/signup", json=payload)
    
    # 3. Verify Response
    if response.status_code != 200:
        logger.error(f"❌ API Failed: {response.text}")
        assert response.status_code == 200
    
    data = response.json()
    logger.info(f"✅ API Response: {data}")
    
    learner_id = data["learner_id"]
    cohort = data["cohort"]
    
    assert learner_id is not None
    assert cohort in ["pilot_treatment", "pilot_control"]
    
    logger.info(f"✅ Learner created: {learner_id} assigned to {cohort}")
    
    # 4. Verify DB Persistence (Async Check)
    asyncio.run(verify_db_persistence(learner_id, cohort))

async def verify_db_persistence(learner_id, cohort_name):
    """
    Directly check Postgres tables to ensure data integrity.
    """
    settings = get_settings()
    dsn = settings.DATABASE_URL
    
    try:
        conn = await asyncpg.connect(dsn)
        logger.info("💾 Connected to DB for verification...")
        
        # Check Learner
        learner = await conn.fetchrow("SELECT * FROM learners WHERE learner_id = $1", learner_id)
        assert learner is not None, "Learner record missing"
        logger.info("✅ Learner record found in 'learners' table")
        
        # Check Consent
        consent = await conn.fetchrow("SELECT * FROM user_consents WHERE learner_id = $1", learner_id)
        assert consent is not None, "Consent record missing"
        assert consent["granted"] is True, "Consent not granted in DB"
        logger.info("✅ Consent record found in 'user_consents' table")
        
        # Check Experiment Assignment
        exp = await conn.fetchrow("""
            SELECT ue.*, eg.name 
            FROM user_experiments ue
            JOIN experiment_groups eg ON ue.group_id = eg.id
            WHERE ue.learner_id = $1
        """, learner_id)
        
        assert exp is not None, "Experiment assignment missing"
        assert exp["name"] == cohort_name, f"Cohort mismatch: DB={exp['name']}, API={cohort_name}"
        logger.info(f"✅ Experiment assignment verified: {exp['name']}")
        
        await conn.close()
        logger.info("🎉 SMOKE TEST PASSED!")
        
    except Exception as e:
        logger.error(f"❌ DB Verification Failed: {e}")
        raise

if __name__ == "__main__":
    try:
        test_learner_signup_flow()
    except Exception as e:
        logger.error(f"💥 Test Failed: {e}")
        exit(1)
