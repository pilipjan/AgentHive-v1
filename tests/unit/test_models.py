"""Unit tests for model schema definitions and column attributes."""

import uuid
from backend.app.models import (
    User,
    Agent,
    AgentPermission,
    Task,
    Message,
    Knowledge,
    ReputationEvent,
    AuditLog,
)


def test_agent_model_columns():
    """Verify column metadata and default definitions on Agent model."""
    assert Agent.status.default.arg == "ACTIVE"
    assert Agent.reputation_score.default.arg == 3.00
    assert Agent.tasks_completed.default.arg == 0
    assert Agent.model_provider.default.arg == "OPENAI"
    assert Agent.model_name.default.arg == "gpt-4o-mini"


def test_task_model_columns():
    """Verify task model column defaults and max iterations."""
    assert Task.status.default.arg == "CREATED"
    assert Task.max_iterations.default.arg == 5


def test_knowledge_model_columns():
    """Verify knowledge model confidence and visibility defaults."""
    assert Knowledge.confidence.default.arg == 0.50
    assert Knowledge.visibility.default.arg == "HIVE"
    assert Knowledge.sensitivity.default.arg == "INTERNAL"
    assert Knowledge.verification_count.default.arg == 0


def test_message_model_columns():
    """Verify message model defaults."""
    assert Message.message_type.default.arg == "DIRECT"
    assert Message.sensitivity.default.arg == "INTERNAL"
    assert Message.authorization_result.default.arg == "ALLOWED"


def test_audit_log_model_columns():
    """Verify audit log status default."""
    assert AuditLog.status.default.arg == "SUCCESS"
