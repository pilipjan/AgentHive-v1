"""Multi-Factor Reputation Calculation Engine."""

from typing import Tuple
from reputation.metrics import AgentPerformanceMetrics, ReputationWeights


class ReputationEngine:
    """Computes tamper-proof multi-factor agent reputation scores."""

    DEFAULT_WEIGHTS = ReputationWeights()

    @classmethod
    def calculate_reputation(
        cls,
        metrics: AgentPerformanceMetrics,
        weights: ReputationWeights = DEFAULT_WEIGHTS,
    ) -> Tuple[float, float]:
        """Compute composite normalized score (0.0 to 1.0) and 1.0-5.0 scale rating."""
        # Baseline normalized score (0.0 to 1.0)
        raw_composite = (
            (metrics.task_success_rate * weights.task_success)
            + (metrics.reviewer_usefulness_score * weights.reviewer_usefulness)
            + (metrics.verification_accuracy_score * weights.verification_accuracy)
            + (metrics.reliability_score * weights.reliability)
            + (metrics.safety_compliance_score * weights.safety)
        )

        # Apply safety violation penalty
        penalty = min(0.5, metrics.security_violations_count * 0.10)
        final_normalized = max(0.0, min(1.0, raw_composite - penalty))

        # Project to 1.00 to 5.00 scale: score = 1.0 + (4.0 * normalized)
        scale_5_score = 1.0 + (4.0 * final_normalized)

        return round(final_normalized, 4), round(scale_5_score, 2)

    @classmethod
    def compute_star_rating(cls, scale_5_score: float) -> float:
        """Round to human-friendly 1-decimal star rating (e.g. 4.87 -> 4.9)."""
        return round(scale_5_score, 1)
