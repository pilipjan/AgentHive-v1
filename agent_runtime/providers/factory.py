"""Model Provider Factory for instantiating provider adapters."""

from typing import Dict, Optional, Type
from agent_runtime.providers.base import BaseModelProvider
from agent_runtime.providers.mock_provider import MockProvider
from agent_runtime.providers.ollama_provider import OllamaProvider
from agent_runtime.providers.openai_provider import OpenAIProvider
from backend.app.core.config import settings


class ModelProviderFactory:
    """Factory creating provider instances dynamically based on provider enum/tag."""

    PROVIDERS: Dict[str, Type[BaseModelProvider]] = {
        "OPENAI": OpenAIProvider,
        "OLLAMA": OllamaProvider,
        "MOCK": MockProvider,
        "ANTHROPIC": MockProvider,  # Fallback to mock in dev/test
        "GEMINI": MockProvider,     # Fallback to mock in dev/test
    }

    @classmethod
    def get_provider(
        cls,
        provider_name: str,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> BaseModelProvider:
        """Instantiate and return model provider adapter."""
        prov_key = provider_name.upper().strip()
        provider_cls = cls.PROVIDERS.get(prov_key, MockProvider)

        # Default model tags
        resolved_model = model_name or ("gpt-4o-mini" if prov_key == "OPENAI" else "gemma2:2b")
        resolved_key = api_key or (getattr(settings, f"{prov_key}_API_KEY", None) if hasattr(settings, f"{prov_key}_API_KEY") else None)
        resolved_url = base_url or (settings.OLLAMA_BASE_URL if prov_key == "OLLAMA" else None)

        return provider_cls(
            model_name=resolved_model,
            api_key=resolved_key,
            base_url=resolved_url,
        )
