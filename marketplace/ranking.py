"""Marketplace Proposal Ranking Engine."""

from typing import List


class ProposalRankingEngine:
    """Ranks competing agent bids using a multi-factor fitness algorithm."""

    @classmethod
    def calculate_bid_score(
        cls,
        agent_reputation: float,  # Scale 1.0 to 5.0
        agent_capabilities: List[str],
        job_requirements: List[str],
        estimated_duration_seconds: int,
    ) -> float:
        """Compute composite bid ranking score (0.0 to 1.0)."""
        # 1. Normalized reputation factor (1.0 to 5.0 -> 0.0 to 1.0)
        rep_normalized = max(0.0, min(1.0, (agent_reputation - 1.0) / 4.0))

        # 2. Capability overlap factor (0.0 to 1.0)
        req_set = {r.strip().lower() for r in job_requirements if r.strip()}
        cap_set = {c.strip().lower() for c in agent_capabilities if c.strip()}

        if not req_set:
            cap_score = 1.0
        else:
            overlap = len(req_set.intersection(cap_set))
            cap_score = min(1.0, overlap / len(req_set))

        # 3. Time efficiency factor (faster execution scores higher, max benchmark 300s)
        time_score = max(0.1, min(1.0, 1.0 - (min(estimated_duration_seconds, 300) / 300.0)))

        # Composite score formula: 50% Reputation + 30% Capability Match + 20% Time Efficiency
        composite = (0.50 * rep_normalized) + (0.30 * cap_score) + (0.20 * time_score)

        return round(composite, 4)
