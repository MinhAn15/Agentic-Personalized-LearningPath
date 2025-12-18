import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class InstructorNotificationService:
    """
    Simulated service to notify instructors/admins about at-risk learners.
    In production, this would send emails, Slack alerts, or update a dashboard.
    """
    
    def __init__(self, output_file: str = "instructor_alerts.log"):
        self.output_file = output_file
        
    async def notify_failure(self, learner_id: str, concept_id: str, score: float, attempts: int):
        """
        Notify when a learner fails a concept assessment critically.
        """
        alert = {
            "type": "CRITICAL_FAILURE",
            "timestamp": datetime.now().isoformat(),
            "learner_id": learner_id,
            "concept_id": concept_id,
            "score": score,
            "attempts": attempts,
            "message": f"Learner {learner_id} failed {concept_id} with score {score:.2f} (Attempt #{attempts}). Intervention recommended."
        }
        
        self._log_alert(alert)
        logger.warning(f"🚨 INSTRUCTOR ALERT: {alert['message']}")
        
    async def notify_stuck(self, learner_id: str, concept_id: str, minutes_spent: int):
        """
        Notify when a learner is spending too much time without progress.
        """
        alert = {
            "type": "LEARNER_STUCK",
            "timestamp": datetime.now().isoformat(),
            "learner_id": learner_id,
            "concept_id": concept_id,
            "minutes_spent": minutes_spent,
            "message": f"Learner {learner_id} has spent {minutes_spent} mins on {concept_id} without mastery."
        }
        
        self._log_alert(alert)
        logger.warning(f"⚠️ INSTRUCTOR ALERT: {alert['message']}")

    def _log_alert(self, alert: Dict[str, Any]):
        """Append alert to a log file (simulating a database/queue)"""
        try:
            with open(self.output_file, "a") as f:
                f.write(json.dumps(alert) + "\n")
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")
