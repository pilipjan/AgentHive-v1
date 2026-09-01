"""Reputation metrics data structures and weights."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ReputationWeights:
    """Configurable weights for the multi-factor reputation algorithm."""

    task_success: float = 0.40
    reviewer_usefulness: float = 0.20
    verification_accuracy: float = 0.15
    reliability: float = 0.15
    safety: float = 0.10

    def to_dict(self) -> Dict[str, float]:
        return {
            "task_success": self.task_success,
            "reviewer_usefulness": self.reviewer_usefulness,
            "verification_accuracy": self.verification_accuracy,
            "reliability": self.reliability,
            "safety": self.safety,
        }


@dataclass
class AgentPerformanceMetrics:
    """Raw underlying evaluation scores (normalized 0.0 to 1.0)."""

    task_success_rate: float
    reviewer_usefulness_score: float
    verification_accuracy_score: float
    reliability_score: float
    safety_compliance_score: float
    total_evaluations_count: int
    security_violations_count: int
