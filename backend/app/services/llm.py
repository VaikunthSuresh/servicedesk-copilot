"""Thin client for any OpenAI-compatible chat endpoint (OpenAI, Groq, Together, Ollama, vLLM...).

If no API key is configured the app still runs: generation falls back to an extractive
answer built from retrieved chunks, so the demo never hard-fails.
"""
import httpx

from ..config import settings


def available() -> bool:
    return bool(settings.llm_api_key) or "localhost" in settings.llm_base_url or "ollama" in settings.llm_base_url


def chat(system: str, user: str, max_tokens: int = 500) -> str:
    headers = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"
    payload = {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    r = httpx.post(f"{settings.llm_base_url.rstrip('/')}/chat/completions", json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()
