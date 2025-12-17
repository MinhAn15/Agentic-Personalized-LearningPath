"""
Mastery Tracker for Evaluator Agent.

Per THESIS Section 3.5.4:
- Weighted moving average: mastery_new = (1-λ)*mastery_old + λ*score
- λ = 0.3 (30% current session, 70% history)
- Bloom-level adjustments for high/low performers
"""

import logging
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class MasteryTracker:
    """
    Track learner mastery using weighted moving average.
    
    Formula: mastery_new = (1-λ) × mastery_old + λ × score_session
    
    Bloom adjustments:
    - Boost +0.05 if score >= 0.9 (ready for next level)
    - Penalty -0.05 if struggling with high-order thinking
    """
    
    LAMBDA_WEIGHT = 0.3  # Weight for current session
    BLOOM_BOOST = 0.05   # Boost when mastery >= 0.9
    BLOOM_PENALTY = 0.05  # Penalty when struggling
    
    # Bloom level hierarchy
    BLOOM_ORDER = ['REMEMBER', 'UNDERSTAND', 'APPLY', 'ANALYZE', 'EVALUATE', 'CREATE']
    HIGH_ORDER_BLOOMS = ['ANALYZE', 'EVALUATE', 'CREATE']
    
    def __init__(self, personal_kg=None, course_kg=None):
        self.personal_kg = personal_kg
        self.course_kg = course_kg
        self.logger = logging.getLogger(f"{__name__}.MasteryTracker")
    
    async def update_mastery(
        self, 
        learner_id: str, 
        concept_id: str,
        score: float, 
        bloom_level: str
    ) -> float:
        """
        Update mastery using weighted moving average.
        
        Args:
            learner_id: Learner UUID
            concept_id: Concept ID
            score: Current session score (0.0-1.0)
            bloom_level: Question's Bloom level
        
        Returns:
            mastery_new (0.0-1.0)
        """
        try:
            # Get current mastery
            mastery_old = await self._get_mastery(learner_id, concept_id)
            if mastery_old is None:
                mastery_old = 0.0
            
            # Weighted moving average
            mastery_new = (1 - self.LAMBDA_WEIGHT) * mastery_old + self.LAMBDA_WEIGHT * score
            
            # Bloom-level adjustment
            mastery_new = self._apply_bloom_adjustment(mastery_new, score, bloom_level)
            
            # Clamp to [0, 1]
            mastery_new = min(1.0, max(0.0, mastery_new))
            
            # Store in Personal KG
            await self._save_mastery(learner_id, concept_id, {
                'mastery_level': mastery_new,
                'bloom_level_achieved': bloom_level,
                'last_score': score,
                'updated_at': datetime.now().isoformat()
            })
            
            self.logger.info(
                f"Updated mastery {learner_id}/{concept_id}: "
                f"{mastery_old:.2f} → {mastery_new:.2f} (score={score:.2f})"
            )
            return mastery_new
        
        except Exception as e:
            self.logger.exception(f"Error updating mastery: {e}")
            return 0.0
    
    def _apply_bloom_adjustment(
        self, 
        mastery: float, 
        score: float, 
        bloom_level: str
    ) -> float:
        """Apply Bloom-level adjustments"""
        # Boost if ready for next Bloom level
        if score >= 0.9 and bloom_level in ['UNDERSTAND', 'APPLY', 'ANALYZE']:
            mastery += self.BLOOM_BOOST
        
        # Penalty if struggling with higher-order thinking
        elif score < 0.4 and bloom_level in self.HIGH_ORDER_BLOOMS:
            mastery -= self.BLOOM_PENALTY
        
        return mastery
    
    async def _get_mastery(self, learner_id: str, concept_id: str) -> Optional[float]:
        """Get current mastery from Personal KG"""
        if not self.personal_kg:
            return None
        
        try:
            if hasattr(self.personal_kg, 'get_mastery'):
                return await self.personal_kg.get_mastery(learner_id, concept_id)
            elif hasattr(self.personal_kg, 'get_context'):
                context = await self.personal_kg.get_context(learner_id, concept_id)
                return context.get('mastery_level') if context else None
        except:
            pass
        
        return None
    
    async def _save_mastery(
        self, 
        learner_id: str, 
        concept_id: str, 
        data: dict
    ):
        """Save mastery to Personal KG"""
        if not self.personal_kg:
            return
        
        try:
            if hasattr(self.personal_kg, 'update_mastery'):
                await self.personal_kg.update_mastery(learner_id, concept_id, data)
            elif hasattr(self.personal_kg, 'set_context'):
                await self.personal_kg.set_context(learner_id, concept_id, data)
        except Exception as e:
            self.logger.warning(f"Failed to save mastery: {e}")
    
    async def get_mastery_trends(
        self, 
        learner_id: str, 
        concept_id: str
    ) -> Dict:
        """
        Get mastery progression history and trends.
        
        Returns:
            {
                'trend': 'MASTERING' | 'PROGRESSING' | 'STRUGGLING' | 'INITIAL',
                'velocity': float (rate of mastery gain),
                'attempts': int,
                'current_mastery': float
            }
        """
        try:
            if not self.personal_kg:
                return {'trend': 'INITIAL', 'velocity': 0.0, 'attempts': 0, 'current_mastery': 0.0}
            
            history = []
            if hasattr(self.personal_kg, 'get_mastery_history'):
                history = await self.personal_kg.get_mastery_history(learner_id, concept_id)
            
            if not history:
                current = await self._get_mastery(learner_id, concept_id) or 0.0
                return {
                    'trend': 'INITIAL', 
                    'velocity': 0.0, 
                    'attempts': 1 if current > 0 else 0,
                    'current_mastery': current
                }
            
            attempts = len(history)
            current_mastery = history[-1].get('mastery', 0.0) if history else 0.0
            
            # Calculate velocity (rate of mastery gain per attempt)
            if attempts >= 2:
                first_mastery = history[0].get('mastery', 0.0)
                velocity = (current_mastery - first_mastery) / attempts
            else:
                velocity = current_mastery
            
            # Determine trend based on recent history
            if attempts >= 3:
                recent = history[-3:]
                recent_avg = sum(h.get('mastery', 0) for h in recent) / 3
                
                if recent_avg >= 0.8:
                    trend = 'MASTERING'
                elif recent_avg >= 0.5:
                    trend = 'PROGRESSING'
                else:
                    trend = 'STRUGGLING'
            else:
                trend = 'INITIAL'
            
            return {
                'trend': trend,
                'velocity': round(velocity, 3),
                'attempts': attempts,
                'current_mastery': current_mastery
            }
        
        except Exception as e:
            self.logger.warning(f"Error getting mastery trends: {e}")
            return {'trend': 'INITIAL', 'velocity': 0.0, 'attempts': 0, 'current_mastery': 0.0}
    
    def compute_learning_velocity(
        self, 
        mastery_history: list, 
        time_history: list = None
    ) -> float:
        """
        Compute learning velocity (mastery gain per unit time/attempt).
        
        Used for personalization and difficulty adjustment.
        """
        if len(mastery_history) < 2:
            return 1.0  # Default velocity
        
        total_gain = mastery_history[-1] - mastery_history[0]
        
        if time_history and len(time_history) >= 2:
            # Time-based velocity
            total_time = sum(time_history)
            return total_gain / max(total_time, 0.1)
        else:
            # Attempt-based velocity
            return total_gain / len(mastery_history)
