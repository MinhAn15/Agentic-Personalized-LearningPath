"""
Global configuration constants for Path Planner Agent.
Per THESIS Section 3.1.x
"""

# ============================================================================
# MASTERY THRESHOLDS
# ============================================================================
MASTERY_PROCEED_THRESHOLD = 0.8  # Evaluator: "PROCEED" if score >= 0.8
MASTERY_PREREQUISITE_THRESHOLD = 0.7  # Can start concept if prereq mastery >= 0.7 (Updated per logic)
MASTERY_REMEDIATE_THRESHOLD = 0.3  # Trigger REMEDIATE if score < 0.3

# ============================================================================
# TUTOR AGENT
# ============================================================================
# Agent 4: Tutor Agent
TUTOR_W_DOC = 0.4
TUTOR_W_KG = 0.35
TUTOR_W_PERSONAL = 0.25
TUTOR_CONFIDENCE_THRESHOLD = 0.5
TUTOR_CONFLICT_THRESHOLD = 0.6
TUTOR_CONFLICT_PENALTY = 0.1

# ============================================================================
# EVALUATOR AGENT
# ============================================================================
# Agent 5: Evaluator Agent
EVAL_MASTERY_WEIGHT = 0.6  # Score weight for WMA
EVAL_DIFFICULTY_ADJUSTMENT = 0.05
EVAL_MASTERY_BOOST = 0.03

# Decision Thresholds
THRESHOLD_MASTERED = 0.9
THRESHOLD_PROCEED = 0.8
THRESHOLD_ALTERNATE = 0.6
THRESHOLD_ALERT = 0.4

# ============================================================================
# KAG AGENT
# ============================================================================
# Agent 6: KAG Agent
KAG_MIN_LEARNERS = 5
KAG_MASTERY_THRESHOLD = 0.8  # Bloom's 2-Sigma (Atomic Note vs Misconception)
KAG_DIFFICULT_THRESHOLD = 0.4  # Avg mastery < 0.4 = Difficult
KAG_EASY_THRESHOLD = 0.8       # Avg mastery > 0.8 = Easy
KAG_PRIORITY_STRUGGLE_THRESHOLD = 0.6  # > 60% struggle = Priority
KAG_MODERATE_STRUGGLE_THRESHOLD = 0.3  # > 30% struggle = Moderate
KAG_STRUGGLE_MASTERY_THRESHOLD = 0.5   # Mastery < 0.5 counts as struggle

# GATE
GATE_FULL_PASS_SCORE = 0.8  # Probabilistic Gate: 100% pass if score >= this

# REVIEW
REVIEW_CHANCE = 0.1  # 10% chance to trigger REVIEW mode on new session

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
