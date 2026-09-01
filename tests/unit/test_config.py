"""Unit tests for configuration loading and defaults."""

from backend.app.core.config import Settings


def test_default_settings():
    """Verify default settings instantiation and types."""
    settings = Settings()
    assert settings.APP_NAME == "AgentHive"
    assert settings.PORT == 8000
    assert settings.MAX_TASK_RECURSION_DEPTH == 5
    assert settings.MEMORY_FIREWALL_STRICT_MODE is True
    assert settings.ENABLE_SIMULATED_TOOLS is True
