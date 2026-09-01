"""Unit tests for LoopDetector, Recursion Limits, and Rate Limiter."""

from agent_runtime.guardrails.loop_detector import LoopDetector
from agent_runtime.guardrails.rate_limiter import RateLimiter


def test_chain_depth_guardrail():
    # Depth 4 < 5 -> Allowed
    res1 = LoopDetector.check_chain_depth(current_depth=4, max_depth=5)
    assert res1.is_loop_detected is False

    # Depth 5 >= 5 -> Blocked
    res2 = LoopDetector.check_chain_depth(current_depth=5, max_depth=5)
    assert res2.is_loop_detected is True
    assert "Maximum task recursion depth" in res2.reason


def test_2_agent_cycle_detection():
    # Ping pong history: [AgentA, AgentB, AgentA, AgentB]
    history = ["agt_alice", "agt_bob", "agt_alice", "agt_bob"]
    res = LoopDetector.check_message_cycle(history)
    assert res.is_loop_detected is True
    assert "Cyclic conversational loop detected" in res.reason


def test_3_agent_cycle_detection():
    # 3-cycle history: [A, B, C, A, B, C]
    history = ["agt_a", "agt_b", "agt_c", "agt_a", "agt_b", "agt_c"]
    res = LoopDetector.check_message_cycle(history)
    assert res.is_loop_detected is True
    assert "3-agent cyclic loop detected" in res.reason


def test_clean_chain_no_loop():
    history = ["agt_a", "agt_b", "agt_c", "agt_d"]
    res = LoopDetector.check_message_cycle(history)
    assert res.is_loop_detected is False


def test_rate_limiter_window():
    limiter = RateLimiter(max_requests=3, window_seconds=10)
    assert limiter.is_allowed("agent-1")[0] is True
    assert limiter.is_allowed("agent-1")[0] is True
    assert limiter.is_allowed("agent-1")[0] is True
    # 4th request in window is rejected
    allowed, retry_after = limiter.is_allowed("agent-1")
    assert allowed is False
    assert retry_after > 0
