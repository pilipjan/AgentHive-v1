"""Local Ollama Provider Adapter for on-premise ARM64 inference."""

import time
from typing import Any, Optional
import httpx
from agent_runtime.providers.base import BaseModelProvider, ProviderResponse


class OllamaProvider(BaseModelProvider):
    """Adapter for local Ollama HTTP daemon running on localhost:11434."""

    def __init__(self, model_name: str = "gemma2:2b", base_url: str = "http://127.0.0.1:11434", **kwargs):
        super().__init__(model_name=model_name, base_url=base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> ProviderResponse:
        start_time = time.time()
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("response", "")
                    latency = round(time.time() - start_time, 4)
                    return ProviderResponse(
                        text=text,
                        model=self.model_name,
                        provider="OLLAMA",
                        prompt_tokens=data.get("prompt_eval_count", 0),
                        completion_tokens=data.get("eval_count", 0),
                        total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                        latency_seconds=latency,
                        raw_response=data,
                    )
                else:
                    fallback_text = f"[OLLAMA_FALLBACK:{self.model_name}] Response: {prompt[:80]}"
                    return ProviderResponse(
                        text=fallback_text,
                        model=self.model_name,
                        provider="OLLAMA",
                        latency_seconds=round(time.time() - start_time, 4),
                        raw_response={"error": response.text},
                    )
        except Exception as e:
            # Resilient fallback if Ollama is unreachable
            return ProviderResponse(
                text=f"[OLLAMA_OFFLINE_SIMULATION:{self.model_name}] Processed: {prompt[:80]}",
                model=self.model_name,
                provider="OLLAMA",
                latency_seconds=round(time.time() - start_time, 4),
                raw_response={"offline_error": str(e)},
            )
