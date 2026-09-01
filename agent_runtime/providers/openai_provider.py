"""OpenAI / OpenRouter Compatible Provider Adapter."""

import time
from typing import Any, Optional
import httpx
from agent_runtime.providers.base import BaseModelProvider, ProviderResponse


class OpenAIProvider(BaseModelProvider):
    """Adapter for OpenAI and OpenAI-compatible endpoints (OpenRouter, LiteLLM, vLLM)."""

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None, base_url: str = "https://api.openai.com/v1", **kwargs):
        super().__init__(model_name=model_name, api_key=api_key, base_url=base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> ProviderResponse:
        start_time = time.time()

        if not self.api_key or self.api_key.startswith("sk-dummy"):
            # Safe simulation when running in test/dev mode without real API key
            reply = f"[OPENAI_SIMULATION:{self.model_name}] Answer for: {prompt[:80]}"
            return ProviderResponse(
                text=reply,
                model=self.model_name,
                provider="OPENAI",
                prompt_tokens=len(prompt.split()),
                completion_tokens=len(reply.split()),
                total_tokens=len(prompt.split()) + len(reply.split()),
                latency_seconds=round(time.time() - start_time, 4),
                raw_response={"simulated": True},
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return ProviderResponse(
                text=text,
                model=self.model_name,
                provider="OPENAI",
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                latency_seconds=round(time.time() - start_time, 4),
                raw_response=data,
            )
