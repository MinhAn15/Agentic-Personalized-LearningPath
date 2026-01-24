import random
import logging
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class ExperimentCohort(str, Enum):
    TREATMENT = "TREATMENT"  # Full Agentic System (Dual KG + Harvard 7)
    CONTROL = "CONTROL"      # Baseline (Simple RAG or Traditional)

class ExperimentManager:
    """
    Manages A/B Testing Experiments for the Pilot.
    
    Responsibilities:
    1. Assign learners to cohorts (Randomized Block Design if needed, or Simple Random)
    2. Ensure cohort balance
    3. Track experiment metadata
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        # Simple in-memory counter for balance checking (in prod, use DB stats)
        self._counts = {ExperimentCohort.TREATMENT: 0, ExperimentCohort.CONTROL: 0}
        
    def assign_cohort(self, learner_profile: Dict[str, Any]) -> ExperimentCohort:
        """
        Assign a learner to a cohort.
        
        Algorithm:
        - Simple Random Assignment (50/50 chance)
        - Can be upgraded to Stratified Randomization (by mastery level)
        """
        # Feature flag: Manual override
        if self.config.get("FORCE_COHORT"):
            return ExperimentCohort(self.config["FORCE_COHORT"])
        
        # Random assignment
        if random.random() < 0.5:
            cohort = ExperimentCohort.TREATMENT
        else:
            cohort = ExperimentCohort.CONTROL
            
        self._counts[cohort] += 1
        logger.info(f"Assigned learner {learner_profile.get('learner_id')} to {cohort.value}")
        return cohort
    
    def get_config_for_cohort(self, cohort: ExperimentCohort) -> Dict[str, bool]:
        """
        Get system configuration based on cohort.
        """
        if cohort == ExperimentCohort.TREATMENT:
            return {
                "use_agents": True,
                "use_dual_kg": True,
                "use_harvard7": True,
                "use_tot": True
            }
        else:
            # Control group: Baseline
            return {
                "use_agents": False, # Or limited agents
                "use_dual_kg": False,
                "use_harvard7": False,
                "use_tot": False
            }

    def log_exposure(self, learner_id: str, cohort: ExperimentCohort):
        """
        Log that a learner has actually been exposed to the treatment.
        Crucial for "Intent-to-Treat" vs "As-Treated" analysis.
        """
        logger.info(f"EXPOSURE_LOG: {learner_id} | {cohort.value} | {datetime.now().isoformat()}")
