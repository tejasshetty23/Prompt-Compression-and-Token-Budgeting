"""Minimal OpenAI-compatible chat-completions client for benchmark inference."""
import json
import os
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

class ChatCompletionClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None,
                 model: str | None = None, timeout: int = 120):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("Set OPENAI_API_KEY before running model-backed benchmarks")

    def answer(self, system_instruction: str, question: str, context: str,
               temperature: float = 0.0) -> dict:
        body = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_instruction or "Answer accurately using the supplied context."},
                {"role": "user", "content": "Context:\n" + context + "\n\nQuestion:\n" + question},
            ],
        }
        request = Request(
            self.base_url + "/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.api_key,
                     "Content-Type": "application/json"},
            method="POST",
        )
        started = perf_counter()
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM API returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach LLM API: {exc.reason}") from exc
        elapsed_ms = (perf_counter() - started) * 1000
        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("LLM API response contained no choices")
        text = choices[0].get("message", {}).get("content", "")
        usage = payload.get("usage") or {}
        return {
            "answer": text,
            "model": payload.get("model", self.model),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "latency_ms": round(elapsed_ms, 3),
        }
