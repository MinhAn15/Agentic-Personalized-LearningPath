import asyncpg
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PostgreSQLClient:
    """
    PostgreSQL client for persistent state storage.
    
    Responsibility:
    - Learner profiles
    - Learning history
    - Evaluation results
    - Session logs
    - Audit trail
    
    Uses asyncpg for async operations (non-blocking).
    """
    
    def __init__(self, dsn: str):
        """
        Initialize PostgreSQL client.
        
        Args:
            dsn: Data Source Name (connection string)
                 Format: postgresql://user:password@host:port/database
        """
        self.dsn = dsn
        self.pool = None
        self.logger = logging.getLogger("PostgreSQLClient")
    
    async def connect(self) -> bool:
        """Create connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            self.logger.info(f"✅ Connected to PostgreSQL pool")
            await self._initialize_schema()
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.logger.info("✅ Disconnected from PostgreSQL")
    
    async def _initialize_schema(self) -> None:
        """Create tables if they don't exist"""
        async with self.pool.acquire() as conn:
            # Learners table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS learners (
                    learner_id VARCHAR(255) PRIMARY KEY,
                    profile JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Learning progress table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS learner_progress (
                    id SERIAL PRIMARY KEY,
                    learner_id VARCHAR(255) REFERENCES learners(learner_id),
                    concept_id VARCHAR(255),
                    mastery FLOAT,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create index for learner_progress
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_learner_concept 
                ON learner_progress (learner_id, concept_id)
            """)
            
            # Learning paths table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_paths (
                    id SERIAL PRIMARY KEY,
                    learner_id VARCHAR(255) REFERENCES learners(learner_id),
                    path JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Evaluation results table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id SERIAL PRIMARY KEY,
                    learner_id VARCHAR(255) REFERENCES learners(learner_id),
                    concept_id VARCHAR(255),
                    score FLOAT,
                    feedback TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Session logs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS session_logs (
                    id SERIAL PRIMARY KEY,
                    learner_id VARCHAR(255) REFERENCES learners(learner_id),
                    agent_id VARCHAR(255),
                    action VARCHAR(255),
                    metadata JSONB,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)

            # --- EXPERIMENT & CONSENT TABLES (Added for Phase 3 Pilot) ---
            
            # Experiment Groups
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS experiment_groups (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    description TEXT,
                    config JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # User Experiment Assignments
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_experiments (
                    id SERIAL PRIMARY KEY,
                    learner_id VARCHAR(255) NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
                    group_id INTEGER NOT NULL REFERENCES experiment_groups(id),
                    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'ACTIVE',
                    CONSTRAINT uq_learner_experiment UNIQUE (learner_id, group_id) 
                )
            """)
            
            # User Consents
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_consents (
                    id SERIAL PRIMARY KEY,
                    learner_id VARCHAR(255) NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
                    consent_version VARCHAR(20) NOT NULL, 
                    granted BOOLEAN NOT NULL,             
                    ip_address VARCHAR(45),               
                    user_agent TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_learner_consent_version UNIQUE (learner_id, consent_version, timestamp)
                )
            """)
            
            # Seed Pilot Groups
            await conn.execute("""
                INSERT INTO experiment_groups (name, description, config)
                VALUES 
                    ('pilot_control', 'Standard Linear Path', '{"adaptive_enabled": false}'),
                    ('pilot_treatment', 'Full Agentic Adaptation', '{"adaptive_enabled": true, "planner_model": "gpt-4"}')
                ON CONFLICT (name) DO NOTHING
            """)
            
            self.logger.info("✅ Schema initialized")
    
    # ============= LEARNER OPERATIONS =============
    
    async def create_learner(self, learner_id: str, profile: Dict) -> bool:
        """Create learner record"""
        try:
            import json
            profile_json = json.dumps(profile)
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO learners (learner_id, profile)
                    VALUES ($1, $2)
                    """,
                    learner_id,
                    profile_json
                )
            self.logger.debug(f"✅ Created learner: {learner_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Create learner failed: {e}")
            return False
    
    async def get_learner(self, learner_id: str) -> Optional[Dict]:
        """Get learner profile"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM learners WHERE learner_id = $1",
                    learner_id
                )
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"❌ Get learner failed: {e}")
            return None
    
    async def update_learner(self, learner_id: str, profile: Dict) -> bool:
        """Update learner profile"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE learners 
                    SET profile = $1, updated_at = NOW()
                    WHERE learner_id = $2
                    """,
                    profile,
                    learner_id
                )
            self.logger.debug(f"✅ Updated learner: {learner_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Update learner failed: {e}")
            return False
    
    # ============= PROGRESS OPERATIONS =============
    
    async def save_progress(
        self,
        learner_id: str,
        concept_id: str,
        mastery: float
    ) -> bool:
        """Save learner's mastery of concept"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO learner_progress 
                    (learner_id, concept_id, mastery)
                    VALUES ($1, $2, $3)
                    """,
                    learner_id,
                    concept_id,
                    mastery
                )
            self.logger.debug(f"✅ Saved progress: {learner_id} → {concept_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Save progress failed: {e}")
            return False
    
    async def get_progress_history(
        self,
        learner_id: str,
        concept_id: str
    ) -> List[Dict]:
        """Get all progress records for concept"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM learner_progress
                    WHERE learner_id = $1 AND concept_id = $2
                    ORDER BY timestamp DESC
                    """,
                    learner_id,
                    concept_id
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"❌ Get progress history failed: {e}")
            return []
    
    # ============= EVALUATION OPERATIONS =============
    
    async def save_evaluation(
        self,
        learner_id: str,
        concept_id: str,
        score: float,
        feedback: str
    ) -> bool:
        """Save evaluation result"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO evaluations 
                    (learner_id, concept_id, score, feedback)
                    VALUES ($1, $2, $3, $4)
                    """,
                    learner_id,
                    concept_id,
                    score,
                    feedback
                )
            self.logger.debug(f"✅ Saved evaluation: {learner_id} → {concept_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Save evaluation failed: {e}")
            return False
    
    async def get_evaluations(self, learner_id: str) -> List[Dict]:
        """Get all evaluations for learner"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM evaluations
                    WHERE learner_id = $1
                    ORDER BY timestamp DESC
                    """,
                    learner_id
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"❌ Get evaluations failed: {e}")
            return []
    
    # ============= EXPERIMENT & CONSENT OPERATIONS =============

    async def record_consent(
        self, 
        learner_id: str, 
        version: str, 
        granted: bool, 
        ip: str = None, 
        user_agent: str = None
    ) -> bool:
        """Record user consent (Immutable Audit Log)"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_consents 
                    (learner_id, consent_version, granted, ip_address, user_agent)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    learner_id, version, granted, ip, user_agent
                )
            self.logger.debug(f"✅ Recorded consent for {learner_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Record consent failed: {e}")
            return False

    async def assign_experiment_group(self, learner_id: str, group_name: str) -> bool:
        """Assign learner to an experiment group by name"""
        try:
            async with self.pool.acquire() as conn:
                # Get Group ID
                group_id = await conn.fetchval(
                    "SELECT id FROM experiment_groups WHERE name = $1", group_name
                )
                if not group_id:
                    self.logger.warning(f"⚠️ Experiment group '{group_name}' not found")
                    return False
                
                # Assign
                await conn.execute(
                    """
                    INSERT INTO user_experiments (learner_id, group_id)
                    VALUES ($1, $2)
                    ON CONFLICT (learner_id, group_id) DO NOTHING
                    """,
                    learner_id, group_id
                )
            self.logger.debug(f"✅ Assigned {learner_id} to {group_name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Assign experiment failed: {e}")
            return False
    
    # ============= GENERIC OPERATIONS =============
    
    async def execute(self, query: str, *args) -> bool:
        """Execute arbitrary query"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, *args)
            return True
        except Exception as e:
            self.logger.error(f"❌ Execute failed: {e}")
            return False
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict]:
        """Fetch single row"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"❌ Fetch one failed: {e}")
            return None
    
    async def fetch_all(self, query: str, *args) -> List[Dict]:
        """Fetch all rows"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"❌ Fetch all failed: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check database connection health"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return False
