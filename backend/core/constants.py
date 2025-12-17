"""
Global configuration constants for Path Planner Agent.
Per THESIS Section 3.1.x
"""

# ============================================================================
# MASTERY THRESHOLDS
# ============================================================================
MASTERY_PROCEED_THRESHOLD = 0.8  # Evaluator: "PROCEED" if score >= 0.8
MASTERY_PREREQUISITE_THRESHOLD = 0.5  # Can start concept if prereq mastery >= 0.5
MASTERY_REMEDIATE_THRESHOLD = 0.3  # Trigger REMEDIATE if score < 0.3

# ============================================================================
# TIME ESTIMATION
# ============================================================================
CONCEPT_BASE_TIME = 0.5  # Base 30 minutes per concept (in hours)
DIFFICULTY_MULTIPLIER = {
    1: 0.5,   # Very easy: 15 min
    2: 0.8,   # Easy: 24 min
    3: 1.0,   # Medium: 30 min
    4: 1.5,   # Hard: 45 min
    5: 2.0    # Very hard: 60 min
}

# ============================================================================
# RL ENGINE
# ============================================================================
UCB_EXPLORATION_CONSTANT = 1.41  # sqrt(2) for UCB1

# ============================================================================
# PATH GENERATION
# ============================================================================
MAX_PATH_CONCEPTS = 50
TIME_BUDGET_FACTOR = 0.9  # Use 90% of available time

# ============================================================================
# PACING DETERMINATION
# ============================================================================
PACING_AGGRESSIVE_THRESHOLD = 0.9  # > 90% time used
PACING_MODERATE_THRESHOLD = 0.7   # > 70% time used
# <= 70% = RELAXED

# ============================================================================
# RELATIONSHIP TYPES (from Agent 1 output)
# ============================================================================
CHAIN_RELATIONSHIPS = {
    "FORWARD": ["NEXT", "IS_PREREQUISITE_OF"],
    "BACKWARD": ["REQUIRES"],
    "LATERAL": ["SIMILAR_TO", "HAS_ALTERNATIVE_PATH", "REMEDIATES"]
}

# ============================================================================
# SUCCESS PROBABILITY WEIGHTS
# ============================================================================
SUCCESS_PROB_MASTERY_WEIGHT = 0.4  # Primary: learner capability
SUCCESS_PROB_TIME_WEIGHT = 0.4  # Secondary: resource availability
SUCCESS_PROB_DIFFICULTY_WEIGHT = 0.2  # Risk: concept hardness
