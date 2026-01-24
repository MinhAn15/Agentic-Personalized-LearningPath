from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import numpy as np
try:
    from scipy import stats
except ImportError:
    stats = None

@dataclass
class LearnerOutcomeMetrics:
    """Metrics for evaluating learning outcomes per ablation study"""
    
    learner_id: str
    course_id: str
    
    # Pre-test / Post-test scores
    pre_test_score: float  # 0-100
    post_test_score: float
    
    # Learning gain (normalized)
    @property
    def learning_gain(self) -> float:
        """Normalized learning gain: (Post - Pre) / (100 - Pre)"""
        # Handle edge cases where Pre is very high (avoid div by zero)
        if self.pre_test_score >= 99.9:
            return 0.0
        # Formula: Hake's normalized gain
        gain = (self.post_test_score - self.pre_test_score) / (100.0 - self.pre_test_score)
        return max(-1.0, min(1.0, gain))
    
    # Time to mastery
    time_to_mastery_min: int  # Minutes spent before hitting mastery threshold
    
    # Retention test (1 month later)
    retention_test_score: float  # 0-100
    
    @property
    def retention_decay(self) -> float:
        """How much was forgotten: (Post - Retention) / Post"""
        if self.post_test_score < 1.0:
            return 0.0
        decay = (self.post_test_score - self.retention_test_score) / self.post_test_score
        return max(0.0, decay)
    
    # Error distribution (by error type)
    error_distribution: Dict[str, int]  # {"CONCEPTUAL": 5, "COMPUTATIONAL": 3, ...}
    
    def to_dict(self) -> Dict:
        return {
            "learner_id": self.learner_id,
            "course_id": self.course_id,
            "pre_test": self.pre_test_score,
            "post_test": self.post_test_score,
            "learning_gain": self.learning_gain,
            "time_to_mastery_min": self.time_to_mastery_min,
            "retention_score": self.retention_test_score,
            "retention_decay": self.retention_decay,
            "error_distribution": self.error_distribution
        }

class LearningOutcomeAnalyzer:
    """Compute statistics and statistical tests on learning outcomes"""
    
    @staticmethod
    def effect_size(treatment_gains: List[float], control_gains: List[float]) -> Dict:
        """
        Compute Cohen's d effect size.
        
        Formula: d = (mean_treatment - mean_control) / pooled_sd
        """
        if not treatment_gains or not control_gains:
            return {"cohens_d": 0.0, "interpretation": "no data"}
            
        mean_t = np.mean(treatment_gains)
        mean_c = np.mean(control_gains)
        
        var_t = np.var(treatment_gains, ddof=1)
        var_c = np.var(control_gains, ddof=1)
        
        n_t = len(treatment_gains)
        n_c = len(control_gains)
        
        denom = n_t + n_c - 2
        if denom <= 0:
            return {"cohens_d": 0.0, "interpretation": "insufficient sample"}
            
        pooled_var = ((n_t - 1) * var_t + (n_c - 1) * var_c) / denom
        pooled_sd = np.sqrt(pooled_var)
        
        if pooled_sd == 0:
            return {"cohens_d": 0.0, "interpretation": "no variance"}
        
        d = (mean_t - mean_c) / pooled_sd
        
        # Interpretation
        if abs(d) < 0.2:
            interpretation = "negligible"
        elif abs(d) < 0.5:
            interpretation = "small"
        elif abs(d) < 0.8:
            interpretation = "medium"
        else:
            interpretation = "large"
        
        return {
            "cohens_d": d,
            "interpretation": interpretation,
            "mean_treatment": mean_t,
            "mean_control": mean_c,
            "pooled_sd": pooled_sd
        }
    
    @staticmethod
    def confidence_interval(values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """Compute confidence interval for mean"""
        if not values:
            return (0.0, 0.0)
            
        mean = np.mean(values)
        if stats:
            se = stats.sem(values)
            ci = se * stats.t.ppf((1 + confidence) / 2, len(values) - 1)
            return (mean - ci, mean + ci)
        else:
            # Fallback if scipy not installed
            std = np.std(values, ddof=1)
            se = std / np.sqrt(len(values))
            return (mean - 1.96 * se, mean + 1.96 * se)
