"""Unit tests for Proposal Ranking Engine."""

from marketplace.ranking import ProposalRankingEngine


def test_perfect_proposal_ranking():
    """Verify high reputation and exact capability match produce a high score."""
    score = ProposalRankingEngine.calculate_bid_score(
        agent_reputation=5.0,
        agent_capabilities=["python", "docker", "fastapi"],
        job_requirements=["python", "fastapi"],
        estimated_duration_seconds=30,
    )
    # Reputation normalized = 1.0 (50% -> 0.50)
    # Capability overlap = 2/2 = 1.0 (30% -> 0.30)
    # Time efficiency = 1 - 30/300 = 0.90 (20% -> 0.18)
    # Total = 0.50 + 0.30 + 0.18 = 0.98
    assert score >= 0.95


def test_partial_capability_match():
    """Verify partial capability match reduces score proportionally."""
    score = ProposalRankingEngine.calculate_bid_score(
        agent_reputation=3.0,
        agent_capabilities=["python"],
        job_requirements=["python", "rust", "cuda", "c++"],
        estimated_duration_seconds=60,
    )
    assert score < 0.60
