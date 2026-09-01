"""Unit tests for ReputationEngine mathematical scoring algorithm."""

from reputation.engine import ReputationEngine
from reputation.metrics import AgentPerformanceMetrics, ReputationWeights


def test_perfect_reputation_calculation():
    """Verify perfect metrics project to 5.0 score and 5.0 star rating."""
    metrics = AgentPerformanceMetrics(
        task_success_rate=1.0,
        reviewer_usefulness_score=1.0,
        verification_accuracy_score=1.0,
        reliability_score=1.0,
        safety_compliance_score=1.0,
        total_evaluations_count=10,
        security_violations_count=0,
    )
    normalized, scale_5 = ReputationEngine.calculate_reputation(metrics)
    assert normalized == 1.0
    assert scale_5 == 5.00
    assert ReputationEngine.compute_star_rating(scale_5) == 5.0


def test_weighted_reputation_calculation():
    """Verify configured weights formula."""
    # (0.40 * 0.9) + (0.20 * 0.8) + (0.15 * 1.0) + (0.15 * 0.9) + (0.10 * 1.0)
    # = 0.36 + 0.16 + 0.15 + 0.135 + 0.10 = 0.905
    # scale_5 = 1.0 + (4.0 * 0.905) = 1.0 + 3.62 = 4.62
    metrics = AgentPerformanceMetrics(
        task_success_rate=0.90,
        reviewer_usefulness_score=0.80,
        verification_accuracy_score=1.00,
        reliability_score=0.90,
        safety_compliance_score=1.00,
        total_evaluations_count=5,
        security_violations_count=0,
    )
    normalized, scale_5 = ReputationEngine.calculate_reputation(metrics)
    assert normalized == 0.905
    assert scale_5 == 4.62
    assert ReputationEngine.compute_star_rating(scale_5) == 4.6


def test_security_violation_penalty():
    """Verify security violations penalize reputation score."""
    clean_metrics = AgentPerformanceMetrics(
        task_success_rate=1.0,
        reviewer_usefulness_score=1.0,
        verification_accuracy_score=1.0,
        reliability_score=1.0,
        safety_compliance_score=1.0,
        total_evaluations_count=10,
        security_violations_count=0,
    )
    _, clean_scale = ReputationEngine.calculate_reputation(clean_metrics)

    violation_metrics = AgentPerformanceMetrics(
        task_success_rate=1.0,
        reviewer_usefulness_score=1.0,
        verification_accuracy_score=1.0,
        reliability_score=1.0,
        safety_compliance_score=1.0,
        total_evaluations_count=10,
        security_violations_count=2,  # 2 * 0.10 = 0.20 penalty
    )
    _, penalized_scale = ReputationEngine.calculate_reputation(violation_metrics)
    assert penalized_scale < clean_scale
    assert penalized_scale == 4.20
