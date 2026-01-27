-- =================================================================
-- APLO Experiment & Consent Schema
-- Purpose: Track A/B test assignments and secure user consent for Pilot
-- Created: 2026-01-26
-- Reviewer: Security Audit (cc-skill-security-review)
-- =================================================================

-- 1. Experiment Groups Configuration
-- Defines the cohorts (e.g., 'Control', 'Adaptive-High-Rate')
CREATE TABLE IF NOT EXISTS experiment_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE, -- e.g. "pilot_v1_control"
    description TEXT,
    config JSONB DEFAULT '{}'::jsonb, -- Store A/B parameters here e.g. {"learning_rate": 0.1}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 2. User Experiment Assignments
-- Links a Learner to a specific Experiment Group
-- Enforces 1 Active Assignment per User per Experiment context (logic handled in app)
CREATE TABLE IF NOT EXISTS user_experiments (
    id SERIAL PRIMARY KEY,
    learner_id VARCHAR(255) NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES experiment_groups(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'COMPLETED', 'DROPPED')),
    
    -- Ensure user is mapped to group uniquely for this assignment record
    CONSTRAINT uq_learner_experiment UNIQUE (learner_id, group_id) 
);

-- Index for fast lookup of user's group during runtime
CREATE INDEX IF NOT EXISTS idx_user_experiments_learner ON user_experiments(learner_id);

-- 3. User Consents (Security & Compliance)
-- MUST be immutable audit log. Do not UPDATE rows here, only INSERT new versions.
CREATE TABLE IF NOT EXISTS user_consents (
    id SERIAL PRIMARY KEY,
    learner_id VARCHAR(255) NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
    consent_version VARCHAR(20) NOT NULL, -- e.g. "v1.0"
    granted BOOLEAN NOT NULL,             -- True = Accepted, False = Rejected/Revoked
    
    -- Audit Trail Fields (PII Protection: strict access control required on this table)
    ip_address VARCHAR(45),               -- IPv4 or IPv6
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Integrity check
    CONSTRAINT uq_learner_consent_version UNIQUE (learner_id, consent_version, timestamp)
);

-- Index for checking latest consent status
CREATE INDEX IF NOT EXISTS idx_consent_learner_latest ON user_consents(learner_id, timestamp DESC);

-- =================================================================
-- Initial Seed Data for Pilot (Optional)
-- =================================================================

-- Insert Pilot Groups if they don't exist
INSERT INTO experiment_groups (name, description, config)
VALUES 
    ('pilot_control', 'Standard Linear Path', '{"adaptive_enabled": false}'),
    ('pilot_treatment', 'Full Agentic Adaptation', '{"adaptive_enabled": true, "planner_model": "gpt-4"}')
ON CONFLICT (name) DO NOTHING;
