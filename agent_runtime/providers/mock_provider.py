"""Deterministic Mock Model Provider for testing and offline environments."""

import time
from typing import Any, Optional
from agent_runtime.providers.base import BaseModelProvider, ProviderResponse


class MockProvider(BaseModelProvider):
    """Deterministic mock provider returning synthesized responses without network calls."""

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> ProviderResponse:
        start_time = time.time()
        reply = f"[MOCK:{self.model_name}] Synthesized response for prompt: {prompt[:60]}..."
        latency = round(time.time() - start_time, 4)

        return ProviderResponse(
            text=reply,
            model=self.model_name,
            provider="MOCK",
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(reply.split()),
            total_tokens=len(prompt.split()) + len(reply.split()),
            latency_seconds=latency,
            raw_response={"mock": True},
        )
