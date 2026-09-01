"""Unit tests for Model Provider Abstraction Layer."""

import pytest
from agent_runtime.providers.factory import ModelProviderFactory
from agent_runtime.providers.mock_provider import MockProvider
from agent_runtime.providers.ollama_provider import OllamaProvider
from agent_runtime.providers.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_mock_provider():
    provider = MockProvider(model_name="test-mock-01")
    res = await provider.generate(prompt="What is the speed of light?")
    assert res.provider == "MOCK"
    assert "speed of light" in res.text
    assert res.total_tokens > 0


@pytest.mark.asyncio
async def test_openai_provider_simulation():
    provider = OpenAIProvider(model_name="gpt-4o-mini", api_key="sk-dummy-key")
    res = await provider.generate(prompt="Analyze this code snippet")
    assert res.provider == "OPENAI"
    assert "Analyze this code snippet" in res.text


@pytest.mark.asyncio
async def test_ollama_provider_offline_fallback():
    provider = OllamaProvider(model_name="gemma2:2b", base_url="http://127.0.0.1:9999")
    res = await provider.generate(prompt="Explain quantum entanglement")
    assert res.provider == "OLLAMA"
    assert res.text is not None


def test_provider_factory():
    p1 = ModelProviderFactory.get_provider("OPENAI", model_name="gpt-4o")
    assert isinstance(p1, OpenAIProvider)
    assert p1.model_name == "gpt-4o"

    p2 = ModelProviderFactory.get_provider("OLLAMA", model_name="llama3.1:8b")
    assert isinstance(p2, OllamaProvider)

    p3 = ModelProviderFactory.get_provider("MOCK")
    assert isinstance(p3, MockProvider)
