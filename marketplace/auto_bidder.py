"""Autonomous Agent Bidding and Proposal Synthesis."""

from typing import Any, Dict
from backend.app.models import Agent, JobPosting
from marketplace.ranking import ProposalRankingEngine


class AutonomousBidder:
    """Generates structured execution proposals on behalf of autonomous agents."""

    @classmethod
    def generate_proposal(cls, agent: Agent, job: JobPosting) -> Dict[str, Any]:
        """Synthesize proposal strategy, estimated duration, and compute bid score."""
        reqs = job.requirements or []
        caps = agent.capabilities or []

        strategy = (
            f"Autonomous execution plan by {agent.name} utilizing {agent.model_provider} ({agent.model_name}). "
            f"Will fulfill prerequisites [{', '.join(reqs)}] through modular decomposition, AST validation, and iterative synthesis."
        )

        # Baseline execution estimate: 15s per requirement tag + 10s base
        estimated_seconds = 10 + (len(reqs) * 15)

        bid_score = ProposalRankingEngine.calculate_bid_score(
            agent_reputation=agent.reputation_score,
            agent_capabilities=caps,
            job_requirements=reqs,
            estimated_duration_seconds=estimated_seconds,
        )

        return {
            "proposed_strategy": strategy,
            "estimated_duration_seconds": estimated_seconds,
            "bid_score": bid_score,
        }
