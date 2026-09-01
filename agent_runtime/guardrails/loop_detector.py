"""Loop Detector & Recursion Guardrails for preventing runaway agent chains and cycles."""

import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class LoopDetectionResult:
    """Verdict from loop inspection."""

    is_loop_detected: bool
    reason: Optional[str] = None
    chain_depth: int = 0


class LoopDetector:
    """Detects infinite conversational ping-pong cycles and enforces maximum execution depths."""

    DEFAULT_MAX_DEPTH = 5
    DEFAULT_MAX_IDENTICAL_MESSAGES = 2

    @classmethod
    def check_chain_depth(cls, current_depth: int, max_depth: int = DEFAULT_MAX_DEPTH) -> LoopDetectionResult:
        """Check if recursion depth exceeds allowable limits."""
        if current_depth >= max_depth:
            return LoopDetectionResult(
                is_loop_detected=True,
                reason=f"Maximum task recursion depth ({max_depth}) exceeded. Aborting to prevent runaway cost.",
                chain_depth=current_depth,
            )
        return LoopDetectionResult(is_loop_detected=False, chain_depth=current_depth)

    @classmethod
    def check_message_cycle(cls, agent_history: List[str]) -> LoopDetectionResult:
        """Detect alternating cyclic loops like [A, B, A, B, A, B]."""
        if len(agent_history) < 4:
            return LoopDetectionResult(is_loop_detected=False, chain_depth=len(agent_history))

        # Check 2-cycle: [A, B, A, B]
        last_4 = agent_history[-4:]
        if last_4[0] == last_4[2] and last_4[1] == last_4[3] and last_4[0] != last_4[1]:
            return LoopDetectionResult(
                is_loop_detected=True,
                reason=f"Cyclic conversational loop detected between {last_4[0]} and {last_4[1]}.",
                chain_depth=len(agent_history),
            )

        # Check 3-cycle: [A, B, C, A, B, C]
        if len(agent_history) >= 6:
            last_6 = agent_history[-6:]
            if last_6[0:3] == last_6[3:6]:
                return LoopDetectionResult(
                    is_loop_detected=True,
                    reason=f"3-agent cyclic loop detected: {' -> '.join(last_6[0:3])}.",
                    chain_depth=len(agent_history),
                )

        return LoopDetectionResult(is_loop_detected=False, chain_depth=len(agent_history))

    @classmethod
    def check_content_repetition(cls, message_hashes: List[str], max_repeats: int = DEFAULT_MAX_IDENTICAL_MESSAGES) -> LoopDetectionResult:
        """Detect identical repeated payloads indicating stuck agent loop."""
        if not message_hashes:
            return LoopDetectionResult(is_loop_detected=False)

        latest = message_hashes[-1]
        repeat_count = message_hashes.count(latest)
        if repeat_count > max_repeats:
            return LoopDetectionResult(
                is_loop_detected=True,
                reason=f"Identical message content generated {repeat_count} times. Halting loop.",
                chain_depth=len(message_hashes),
            )

        return LoopDetectionResult(is_loop_detected=False, chain_depth=len(message_hashes))
