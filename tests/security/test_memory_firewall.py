"""Security tests for the 6-stage Memory Firewall pipeline."""

from security.permissions.enums import PolicyVerdict, SensitivityTier, VisibilityScope
from security.firewall.pipeline import MemoryFirewall


def test_clean_message_is_allowed():
    res = MemoryFirewall.process_message(
        content="I have reviewed the task specs and the benchmark completed in 4.2 seconds.",
        sender_id="agt-worker-01",
        sender_permissions=["MESSAGE_AGENTS"],
        is_same_hive=True,
    )
    assert res.verdict == PolicyVerdict.ALLOWED
    assert res.sensitivity == SensitivityTier.PUBLIC
    assert "benchmark completed in 4.2 seconds" in res.sanitized_text


def test_message_with_secrets_and_pii_is_redacted():
    res = MemoryFirewall.process_message(
        content="Contact me at dev@domain.com or use key sk-1234567890abcdef1234567890 for API testing.",
        sender_id="agt-worker-01",
        sender_permissions=["MESSAGE_AGENTS"],
        is_same_hive=True,
    )
    assert res.verdict == PolicyVerdict.REDACTED
    assert "OPENAI_API_KEY" in res.detected_secrets
    assert "EMAIL" in res.detected_pii
    assert "[REDACTED_EMAIL]" in res.sanitized_text
    assert "[REDACTED_SECRET:OPENAI_API_KEY]" in res.sanitized_text
    assert "sk-1234567890abcdef1234567890" not in res.sanitized_text


def test_message_with_private_key_is_blocked():
    res = MemoryFirewall.process_message(
        content="Here is the server key: -----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0Y...\n-----END RSA PRIVATE KEY-----",
        sender_id="agt-worker-01",
        sender_permissions=["MESSAGE_AGENTS"],
        is_same_hive=True,
    )
    assert res.verdict == PolicyVerdict.BLOCKED
    assert "PRIVATE_KEY" in res.detected_secrets
    assert res.sanitized_text == ""


def test_unauthorized_message_is_blocked():
    res = MemoryFirewall.process_message(
        content="Hello peer agent",
        sender_id="agt-worker-01",
        sender_permissions=[],  # Lacks MESSAGE_AGENTS
        is_same_hive=True,
    )
    assert res.verdict == PolicyVerdict.BLOCKED
    assert "MESSAGE_AGENTS" in res.rejection_reason


def test_public_knowledge_with_secrets_is_blocked():
    res = MemoryFirewall.process_knowledge(
        summary="API configuration guide",
        content="Set key to sk-proj-1234567890abcdefghijklmnopqrstuvwxyz01234567890",
        source_agent_id="agt-worker-01",
        source_permissions=["WRITE_KNOWLEDGE", "READ_PUBLIC_KNOWLEDGE"],
        target_visibility=VisibilityScope.PUBLIC,
    )
    assert res.verdict == PolicyVerdict.BLOCKED
    assert "cannot contain raw credentials" in res.rejection_reason
